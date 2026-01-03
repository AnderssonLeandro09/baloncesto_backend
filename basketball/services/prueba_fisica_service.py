"""Servicio de negocio para Prueba Física."""

import logging
import requests
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from ..dao.prueba_fisica_dao import PruebaFisicaDAO
from ..dao.atleta_dao import AtletaDAO
from ..models import PruebaFisica, Entrenador

logger = logging.getLogger(__name__)


class PruebaFisicaService:
    """Lógica de negocio para pruebas físicas."""

    def __init__(self):
        self.dao = PruebaFisicaDAO()
        self.atleta_dao = AtletaDAO()
        self.user_module_url = settings.USER_MODULE_URL.rstrip("/")

    @staticmethod
    def calcular_semestre(fecha_registro) -> str:
        """Calcula el semestre automáticamente desde la fecha de registro.
        Formato: YYYY-1 (Enero-Junio) o YYYY-2 (Julio-Diciembre)

        Args:
            fecha_registro: Fecha de registro de la prueba (date object)

        Returns:
            String en formato 'YYYY-1' o 'YYYY-2'
        """
        if not fecha_registro:
            return "N/A"
        year = fecha_registro.year
        # Enero (1) a Junio (6) = Semestre 1
        # Julio (7) a Diciembre (12) = Semestre 2
        periodo = 1 if fecha_registro.month <= 6 else 2
        return f"{year}-{periodo}"

    def _build_auth_header(self, token: Optional[str]) -> Dict[str, str]:
        if not token:
            raise PermissionDenied("Token de autenticacion requerido")
        bearer = token if token.startswith("Bearer ") else f"Bearer {token}"
        return {"Authorization": bearer}

    def _call_user_module(
        self,
        method: str,
        path: str,
        token: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = self._build_auth_header(token)
        url = f"{self.user_module_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=8,
            )
        except requests.RequestException as exc:
            logger.error("Fallo al invocar user_module %s: %s", url, exc)
            raise ValidationError("No se pudo contactar al módulo de usuarios")

        if response.status_code in (401, 403):
            raise PermissionDenied("Token sin permisos en módulo de usuarios")

        if response.status_code >= 400:
            logger.error(
                "Error en módulo de usuarios: %s - %s",
                response.status_code,
                response.text,
            )
            raise ValidationError("Error en la comunicación con el módulo de usuarios")

        try:
            return response.json()
        except ValueError:
            raise ValidationError("Respuesta inválida del módulo de usuarios")

    def _fetch_persona(
        self, persona_external: str, token: str, allow_fail: bool = False
    ) -> Optional[Dict[str, Any]]:
        if not persona_external:
            return None
        try:
            response = self._call_user_module(
                "get", f"/api/person/search/{persona_external}", token
            )
            persona_data = response.get("data") if isinstance(response, dict) else None
            if persona_data:
                return {
                    "nombre": persona_data.get("firts_name"),
                    "apellido": persona_data.get("last_name"),
                    "identificacion": persona_data.get("identification"),
                }
            return None
        except Exception as exc:
            if allow_fail:
                return None
            raise ValidationError(f"No se pudo obtener datos de la persona: {exc}")

    def _get_filtered_queryset(self, user):
        """Retorna el queryset de pruebas físicas filtrado por permisos del usuario."""
        queryset = self.dao.get_by_filter(estado=True).select_related("atleta")

        if not user or not hasattr(user, "role"):
            return queryset.none()

        # Si es ESTUDIANTE_VINCULACION, puede ver todo
        if user.role == "ESTUDIANTE_VINCULACION":
            return queryset

        # Si es ENTRENADOR, solo ve atletas de sus grupos
        if user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if not entrenador:
                return queryset.none()
            return queryset.filter(atleta__grupos__entrenador=entrenador).distinct()

        return queryset.none()

    def get_all_pruebas_fisicas_completas(
        self, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """Obtiene todas las pruebas físicas con datos de persona."""
        pruebas = self._get_filtered_queryset(user)
        results = []
        for prueba in pruebas:
            persona_info = self._fetch_persona(
                prueba.atleta.persona_external, token, allow_fail=True
            )
            results.append(
                {
                    "id": prueba.id,
                    "atleta": prueba.atleta.id,
                    "persona": persona_info,
                    "fecha_registro": prueba.fecha_registro,
                    "tipo_prueba": prueba.tipo_prueba,
                    "resultado": prueba.resultado,
                    "unidad_medida": prueba.unidad_medida,
                    "observaciones": prueba.observaciones,
                    "estado": prueba.estado,
                    "semestre": self.calcular_semestre(prueba.fecha_registro),
                }
            )
        return results

    def get_prueba_fisica_completa(
        self, prueba_id: int, token: str, user=None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una prueba física completa por ID."""
        prueba = self._get_filtered_queryset(user).filter(id=prueba_id).first()
        if not prueba:
            return None

        persona_info = self._fetch_persona(
            prueba.atleta.persona_external, token, allow_fail=True
        )
        return {
            "id": prueba.id,
            "atleta": prueba.atleta.id,
            "persona": persona_info,
            "fecha_registro": prueba.fecha_registro,
            "semestre": self.calcular_semestre(prueba.fecha_registro),
            "tipo_prueba": prueba.tipo_prueba,
            "resultado": prueba.resultado,
            "unidad_medida": prueba.unidad_medida,
            "observaciones": prueba.observaciones,
            "estado": prueba.estado,
        }

    def create_prueba_fisica(self, data: dict, user=None) -> PruebaFisica:
        """Crea una nueva prueba física."""
        try:
            atleta_id = data.pop("atleta_id", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")

            # Validar que atleta_id sea un entero válido y en rango razonable
            try:
                atleta_id = int(atleta_id)
                if atleta_id <= 0 or atleta_id > 2147483647:  # Máximo INT en PostgreSQL
                    raise ValidationError(
                        "El ID del atleta está fuera del rango permitido"
                    )
            except (TypeError, ValueError):
                raise ValidationError("El ID del atleta debe ser un número válido")

            # Validar existencia del atleta
            atleta = self.atleta_dao.get_by_id(atleta_id)
            if not atleta:
                raise ValidationError(f"El atleta con ID {atleta_id} no existe")

            # Validar que el atleta tenga inscripción habilitada
            if not hasattr(atleta, "inscripcion") or not atleta.inscripcion.habilitada:
                raise ValidationError("El atleta no tiene inscripción habilitada")

            # Validar autorización
            if user and user.role == "ENTRENADOR":
                entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
                if (
                    not entrenador
                    or not atleta.grupos.filter(entrenador=entrenador).exists()
                ):
                    raise PermissionDenied(
                        "No tiene permiso para registrar pruebas a este atleta"
                    )
            elif user and user.role != "ESTUDIANTE_VINCULACION":
                raise PermissionDenied("No tiene permiso para realizar esta acción")

            # Validar fecha no futura
            fecha_registro = data.get("fecha_registro")
            from datetime import date

            if fecha_registro and fecha_registro > date.today():
                raise ValidationError("La fecha de registro no puede ser futura")

            # Validar resultado (debe ser positivo y en rango razonable)
            resultado = data.get("resultado")
            if resultado is not None:
                try:
                    resultado_float = float(resultado)
                    if resultado_float <= 0:
                        raise ValidationError("El resultado debe ser mayor a 0")
                    if resultado_float > 999999:  # Límite razonable
                        raise ValidationError(
                            "El resultado excede el valor máximo permitido"
                        )
                except (TypeError, ValueError):
                    raise ValidationError("El resultado debe ser un número válido")

            # Validar tipo de prueba
            tipo_prueba = data.get("tipo_prueba")
            if not tipo_prueba:
                raise ValidationError("El tipo de prueba es requerido")

            # Validar y sanitizar observaciones
            observaciones = data.get("observaciones")
            if observaciones:
                observaciones = str(observaciones).strip()
                if len(observaciones) > 1000:
                    raise ValidationError(
                        "Las observaciones no pueden exceder 1000 caracteres"
                    )
                # Sanitización adicional ya se hace en el serializer
                data["observaciones"] = observaciones

            # Asignar unidad de medida automáticamente según el tipo de prueba
            data["unidad_medida"] = PruebaFisica.get_unidad_por_tipo(tipo_prueba)

            data["atleta_id"] = atleta_id
            return self.dao.create(**data)
        except (ValidationError, PermissionDenied):
            raise
        except Exception:
            logger.error("Error al crear prueba física", exc_info=True)
            raise ValidationError("No se pudo crear la prueba física")

    def update_prueba_fisica(
        self, prueba_id: int, data: dict, user=None
    ) -> PruebaFisica:
        """Actualiza una prueba física existente."""
        try:
            # Validar que prueba_id sea un entero válido y en rango razonable
            try:
                prueba_id = int(prueba_id)
                if prueba_id <= 0 or prueba_id > 2147483647:
                    raise ValidationError(
                        "El ID de la prueba está fuera del rango permitido"
                    )
            except (TypeError, ValueError):
                raise ValidationError("El ID de la prueba debe ser un número válido")

            # Validar existencia y autorización
            prueba = self.dao.get_by_id(prueba_id)
            if not prueba:
                raise ValidationError("Prueba física no encontrada")

            # Validar que la prueba esté activa
            if not prueba.estado:
                raise ValidationError("No se puede modificar una prueba inactiva")

            if user and user.role == "ENTRENADOR":
                entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
                if (
                    not entrenador
                    or not prueba.atleta.grupos.filter(entrenador=entrenador).exists()
                ):
                    raise PermissionDenied(
                        "No tiene permiso para modificar esta prueba"
                    )
            elif user and user.role != "ESTUDIANTE_VINCULACION":
                raise PermissionDenied("No tiene permiso para realizar esta acción")

            # No permitimos cambiar el atleta en una actualización por seguridad
            data.pop("atleta_id", None)
            # No permitir cambiar la fecha de registro en actualización
            data.pop("fecha_registro", None)

            # Validar resultado si se está actualizando
            resultado = data.get("resultado")
            if resultado is not None:
                try:
                    resultado_float = float(resultado)
                    if resultado_float <= 0:
                        raise ValidationError("El resultado debe ser mayor a 0")
                    if resultado_float > 999999:
                        raise ValidationError(
                            "El resultado excede el valor máximo permitido"
                        )
                except (TypeError, ValueError):
                    raise ValidationError("El resultado debe ser un número válido")

            # Validar y sanitizar observaciones si se están actualizando
            observaciones = data.get("observaciones")
            if observaciones is not None:
                observaciones = str(observaciones).strip()
                if len(observaciones) > 1000:
                    raise ValidationError(
                        "Las observaciones no pueden exceder 1000 caracteres"
                    )
                data["observaciones"] = observaciones

            # Asignar unidad de medida automáticamente si se está cambiando el tipo de prueba
            tipo_prueba = data.get("tipo_prueba")
            if tipo_prueba:
                data["unidad_medida"] = PruebaFisica.get_unidad_por_tipo(tipo_prueba)

            return self.dao.update(prueba_id, **data)
        except (ValidationError, PermissionDenied):
            raise
        except Exception:
            logger.error("Error al actualizar prueba física", exc_info=True)
            raise ValidationError("No se pudo actualizar la prueba física")

    def get_prueba_fisica_by_id(self, prueba_id: int) -> Optional[PruebaFisica]:
        """Obtiene una prueba física por su ID."""
        return self.dao.get_by_id(prueba_id)

    def get_all_pruebas_fisicas(self) -> List[PruebaFisica]:
        """Obtiene todas las pruebas físicas activas."""
        return list(self.dao.get_by_filter(estado=True))

    def get_pruebas_by_atleta_completas(
        self, atleta_id: int, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """Obtiene todas las pruebas físicas de un atleta con datos de persona."""
        pruebas = self._get_filtered_queryset(user).filter(atleta_id=atleta_id)
        results = []
        for prueba in pruebas:
            persona_info = self._fetch_persona(
                prueba.atleta.persona_external, token, allow_fail=True
            )
            results.append(
                {
                    "id": prueba.id,
                    "atleta": prueba.atleta.id,
                    "persona": persona_info,
                    "fecha_registro": prueba.fecha_registro,
                    "semestre": self.calcular_semestre(prueba.fecha_registro),
                    "tipo_prueba": prueba.tipo_prueba,
                    "resultado": prueba.resultado,
                    "unidad_medida": prueba.unidad_medida,
                    "observaciones": prueba.observaciones,
                    "estado": prueba.estado,
                }
            )
        return results

    def toggle_estado(self, prueba_id: int, user=None) -> PruebaFisica:
        """Cambia el estado de una prueba física (True -> False o viceversa)."""
        # Validar que prueba_id sea un entero válido
        try:
            prueba_id = int(prueba_id)
        except (TypeError, ValueError):
            raise ValidationError("El ID de la prueba debe ser un número válido")

        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError("Prueba física no encontrada")

        # Validar autorización
        if user and user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if (
                not entrenador
                or not prueba.atleta.grupos.filter(entrenador=entrenador).exists()
            ):
                raise PermissionDenied("No tiene permiso para modificar esta prueba")
        elif user and user.role != "ESTUDIANTE_VINCULACION":
            raise PermissionDenied("No tiene permiso para realizar esta acción")

        return self.dao.update(prueba_id, estado=not prueba.estado)

    def get_atletas_habilitados_con_persona(
        self, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """Obtiene atletas con inscripción habilitada y sus datos de persona."""
        from ..models import Atleta

        # Filtrar atletas que tengan inscripción habilitada
        queryset = Atleta.objects.filter(inscripcion__habilitada=True)

        # Si es entrenador, filtrar por sus grupos
        if user and user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if entrenador:
                queryset = queryset.filter(grupos__entrenador=entrenador).distinct()
            else:
                return []

        results = []
        for atleta in queryset:
            persona_info = self._fetch_persona(
                atleta.persona_external, token, allow_fail=True
            )

            results.append(
                {
                    "id": atleta.id,
                    "persona": persona_info,
                    "persona_external": atleta.persona_external,
                }
            )
        return results
