"""Servicio de negocio para Prueba Física."""

import logging
import requests
from datetime import date
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from ..dao.prueba_fisica_dao import PruebaFisicaDAO
from ..dao.atleta_dao import AtletaDAO
from ..models import PruebaFisica, Entrenador

logger = logging.getLogger(__name__)

# Constantes para mensajes de error
MSG_SIN_PERMISO_ACCION = "No tiene permiso para realizar esta acción"
MSG_SIN_PERMISO_MODIFICAR = "No tiene permiso para modificar esta prueba"
MSG_SIN_PERMISO_REGISTRAR = "No tiene permiso para registrar pruebas a este atleta"
MSG_PRUEBA_NO_ENCONTRADA = "Prueba física no encontrada"
MSG_ID_INVALIDO = "El ID de la prueba debe ser un número válido"
MSG_ID_FUERA_RANGO = "El ID de la prueba está fuera del rango permitido"

# Rangos máximos por tipo de prueba (baloncesto)
RANGOS_MAXIMOS = {
    "FUERZA": 300,  # Salto horizontal: hasta 300 cm
    "VELOCIDAD": 15,  # 30m velocidad: hasta ~15 seg (margen amplio)
    "AGILIDAD": 25,  # Zigzag: hasta ~25 seg (margen amplio)
}

# Límite máximo de ID en PostgreSQL
MAX_INT_ID = 2147483647


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
                    "nombre": persona_data.get("first_name")
                    or persona_data.get("firts_name"),
                    "apellido": persona_data.get("last_name"),
                    "identificacion": persona_data.get("identification"),
                }
            return None
        except Exception as exc:
            if allow_fail:
                return None
            raise ValidationError(f"No se pudo obtener datos de la persona: {exc}")

    def _get_persona_info(self, atleta, token: str) -> Dict[str, Any]:
        """Obtiene información de la persona con fallback a datos locales."""
        persona_info = self._fetch_persona(
            atleta.persona_external, token, allow_fail=True
        )

        if not persona_info:
            return {
                "nombre": atleta.nombres or "Atleta",
                "apellido": atleta.apellidos or f"ID: {atleta.id}",
                "identificacion": atleta.cedula or "N/A",
            }

        if not persona_info.get("nombre") and atleta.nombres:
            persona_info["nombre"] = atleta.nombres
        if not persona_info.get("apellido") and atleta.apellidos:
            persona_info["apellido"] = atleta.apellidos
        if not persona_info.get("identificacion") and atleta.cedula:
            persona_info["identificacion"] = atleta.cedula

        return persona_info

    def _get_filtered_queryset(self, user):
        """Retorna el queryset de pruebas físicas filtrado por permisos del usuario."""
        queryset = self.dao.get_all().select_related("atleta")

        if not user or not hasattr(user, "role"):
            return queryset.none()

        if user.role == "ESTUDIANTE_VINCULACION":
            return queryset

        if user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if not entrenador:
                return queryset.none()
            return queryset.filter(atleta__grupos__entrenador=entrenador).distinct()

        return queryset.none()

    def _build_prueba_dict(
        self, prueba, persona_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Construye el diccionario de respuesta para una prueba física."""
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

    def _validate_int_id(self, id_value, field_name: str = "ID") -> int:
        """Valida y convierte un ID a entero."""
        try:
            id_int = int(id_value)
            if id_int <= 0 or id_int > MAX_INT_ID:
                raise ValidationError(f"El {field_name} está fuera del rango permitido")
            return id_int
        except (TypeError, ValueError):
            raise ValidationError(f"El {field_name} debe ser un número válido")

    def _validate_resultado(self, resultado, tipo_prueba: str) -> None:
        """Valida el resultado de una prueba física."""
        if resultado is None:
            return

        try:
            resultado_float = float(resultado)
        except (TypeError, ValueError):
            raise ValidationError("El resultado debe ser un número válido")

        if resultado_float <= 0:
            raise ValidationError(
                "No se permiten valores negativos o cero. El resultado debe ser mayor a 0"
            )

        rango_max = RANGOS_MAXIMOS.get(tipo_prueba, 999999)
        if resultado_float > rango_max:
            raise ValidationError(
                f"El resultado excede el rango máximo permitido para {tipo_prueba}: {rango_max}"
            )

    def _validate_observaciones(self, observaciones: Optional[str]) -> Optional[str]:
        """Valida y sanitiza las observaciones."""
        if not observaciones:
            return observaciones

        observaciones = str(observaciones).strip()
        if len(observaciones) > 200:
            raise ValidationError("Las observaciones no pueden exceder 200 caracteres")
        return observaciones

    def _check_user_permission_for_atleta(self, user, atleta) -> None:
        """Verifica si el usuario tiene permiso para acceder al atleta."""
        if not user:
            return

        if user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if (
                not entrenador
                or not atleta.grupos.filter(entrenador=entrenador).exists()
            ):
                raise PermissionDenied(MSG_SIN_PERMISO_REGISTRAR)
        elif user.role != "ESTUDIANTE_VINCULACION":
            raise PermissionDenied(MSG_SIN_PERMISO_ACCION)

    def _check_user_permission_for_prueba(self, user, prueba) -> None:
        """Verifica si el usuario tiene permiso para modificar la prueba."""
        if not user:
            return

        if user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if (
                not entrenador
                or not prueba.atleta.grupos.filter(entrenador=entrenador).exists()
            ):
                raise PermissionDenied(MSG_SIN_PERMISO_MODIFICAR)
        elif user.role != "ESTUDIANTE_VINCULACION":
            raise PermissionDenied(MSG_SIN_PERMISO_ACCION)

    def get_all_pruebas_fisicas_completas(
        self, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """Obtiene todas las pruebas físicas con datos de persona."""
        pruebas = self._get_filtered_queryset(user)
        results = []
        for prueba in pruebas:
            persona_info = self._get_persona_info(prueba.atleta, token)
            results.append(self._build_prueba_dict(prueba, persona_info))
        return results

    def get_prueba_fisica_completa(
        self, prueba_id: int, token: str, user=None
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una prueba física completa por ID."""
        prueba = self._get_filtered_queryset(user).filter(id=prueba_id).first()
        if not prueba:
            return None

        persona_info = self._get_persona_info(prueba.atleta, token)
        return self._build_prueba_dict(prueba, persona_info)

    def create_prueba_fisica(self, data: dict, user=None) -> PruebaFisica:
        """Crea una nueva prueba física."""
        try:
            atleta_id = data.pop("atleta_id", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")

            atleta_id = self._validate_int_id(atleta_id, "ID del atleta")

            atleta = self.atleta_dao.get_by_id(atleta_id)
            if not atleta:
                raise ValidationError(f"El atleta con ID {atleta_id} no existe")

            if not hasattr(atleta, "inscripcion") or not atleta.inscripcion.habilitada:
                raise ValidationError(
                    '"El atleta no tiene inscripción habilitada". No se guarda el registro.'
                )

            self._check_user_permission_for_atleta(user, atleta)

            fecha_registro = data.get("fecha_registro")
            if not fecha_registro:
                fecha_registro = date.today()
                data["fecha_registro"] = fecha_registro
            elif fecha_registro > date.today():
                raise ValidationError("La fecha de registro no puede ser futura")

            tipo_prueba = data.get("tipo_prueba")
            if not tipo_prueba:
                raise ValidationError("El tipo de prueba es requerido")

            self._validate_resultado(data.get("resultado"), tipo_prueba)

            observaciones = self._validate_observaciones(data.get("observaciones"))
            if observaciones is not None:
                data["observaciones"] = observaciones

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
            prueba_id = self._validate_int_id(prueba_id, "ID de la prueba")

            prueba = self.dao.get_by_id(prueba_id)
            if not prueba:
                raise ValidationError(MSG_PRUEBA_NO_ENCONTRADA)

            if not prueba.estado:
                raise ValidationError("No se puede modificar una prueba inactiva")

            self._check_user_permission_for_prueba(user, prueba)

            data.pop("atleta_id", None)
            data.pop("fecha_registro", None)

            tipo_actual = data.get("tipo_prueba") or prueba.tipo_prueba
            self._validate_resultado(data.get("resultado"), tipo_actual)

            observaciones = data.get("observaciones")
            if observaciones is not None:
                data["observaciones"] = self._validate_observaciones(observaciones)

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
            persona_info = self._get_persona_info(prueba.atleta, token)
            results.append(self._build_prueba_dict(prueba, persona_info))
        return results

    def toggle_estado(self, prueba_id: int, user=None) -> PruebaFisica:
        """Cambia el estado de una prueba física (True -> False o viceversa)."""
        prueba_id = self._validate_int_id(prueba_id, "ID de la prueba")

        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError(MSG_PRUEBA_NO_ENCONTRADA)

        self._check_user_permission_for_prueba(user, prueba)

        return self.dao.update(prueba_id, estado=not prueba.estado)

    def get_atletas_habilitados_con_persona(
        self, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """Obtiene atletas con inscripción habilitada y sus datos de persona."""
        from ..models import Atleta

        queryset = Atleta.objects.filter(inscripcion__habilitada=True)

        if user and user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if entrenador:
                queryset = queryset.filter(grupos__entrenador=entrenador).distinct()
            else:
                return []

        results = []
        for atleta in queryset:
            persona_info = self._get_persona_info(atleta, token)
            results.append(
                {
                    "id": atleta.id,
                    "persona": persona_info,
                    "persona_external": atleta.persona_external,
                }
            )
        return results
