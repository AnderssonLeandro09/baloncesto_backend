"""Servicio de negocio para Prueba Antropométrica."""

import logging
import requests
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from ..dao.prueba_antropometrica_dao import PruebaAntropometricaDAO
from ..models import Atleta, Entrenador, PruebaAntropometrica

logger = logging.getLogger(__name__)


class PruebaAntropometricaService:
    """Lógica de negocio para pruebas antropométricas."""

    def __init__(self):
        self.dao = PruebaAntropometricaDAO()

    def get_all_pruebas_antropometricas(self) -> List[PruebaAntropometrica]:
        """Obtiene todas las pruebas antropométricas."""
        return list(self.dao.get_all())

    def get_prueba_antropometrica_by_id(
        self, pk: int
    ) -> Optional[PruebaAntropometrica]:
        """Obtiene una prueba antropométrica por su ID."""
        return self.dao.get_by_id(pk)

    def create_prueba_antropometrica(self, data: dict, user) -> PruebaAntropometrica:
        """Crea una nueva prueba antropométrica."""
        try:
            # Soportar tanto 'atleta_id' como 'atleta' del frontend
            atleta_id = data.pop("atleta_id", None) or data.pop("atleta", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")

            if not Atleta.objects.filter(id=atleta_id).exists():
                raise ValidationError("El atleta no existe")

            # Determinar tipo de registrador
            registrador = None
            rol = "ENTRENADOR"
            content_type = None
            object_id = None

            if hasattr(user, "entrenador"):
                registrador = user.entrenador
                rol = "ENTRENADOR"
                content_type = ContentType.objects.get_for_model(registrador.__class__)
                object_id = registrador.id
            elif hasattr(user, "estudiantevinculacion"):
                registrador = user.estudiantevinculacion
                rol = "ESTUDIANTE_VINCULACION"
                content_type = ContentType.objects.get_for_model(registrador.__class__)
                object_id = registrador.id

            data.update(
                {
                    "atleta_id": atleta_id,
                    "content_type": content_type,
                    "object_id": object_id,
                    "rol_registrador": rol,
                }
            )

            return self.dao.create(**data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al crear prueba antropométrica: {e}")
            raise ValidationError(
                f"No se pudo crear la prueba antropométrica: {str(e)}"
            )

    def update_prueba_antropometrica(
        self, pk: int, data: dict, user
    ) -> PruebaAntropometrica:
        """Actualiza una prueba antropométrica existente."""
        try:
            prueba = self.dao.get_by_id(pk)
            if not prueba:
                raise ValidationError("Prueba antropométrica no encontrada")

            # Soportar tanto 'atleta_id' como 'atleta' del frontend
            atleta_id = data.pop("atleta_id", None) or data.pop("atleta", None)
            if atleta_id:
                if not Atleta.objects.filter(id=atleta_id).exists():
                    raise ValidationError("El atleta no existe")
                data["atleta_id"] = atleta_id

            return self.dao.update(pk, **data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar prueba antropométrica: {e}")
            raise ValidationError(
                f"No se pudo actualizar la prueba antropométrica: {str(e)}"
            )

    def get_pruebas_antropometricas_by_atleta(
        self, atleta_id: int
    ) -> List[PruebaAntropometrica]:
        """Obtiene todas las pruebas antropométricas de un atleta específico."""
        return list(self.dao.get_by_atleta(atleta_id))

    def get_pruebas_by_atleta(self, atleta_id: int) -> List[PruebaAntropometrica]:
        """Alias requerido por los tests; delega en el método principal."""
        return self.get_pruebas_antropometricas_by_atleta(atleta_id)

    def toggle_estado(self, prueba_id: int) -> PruebaAntropometrica:
        """Cambia el estado de una prueba antropométrica (True -> False o viceversa)."""
        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError("Prueba antropométrica no encontrada")

        return self.dao.update(prueba_id, estado=not prueba.estado)

    def _call_user_module(
        self,
        method: str,
        path: str,
        token: str,
    ) -> Dict[str, Any]:
        """Llama al módulo de usuarios."""
        user_module_url = settings.USER_MODULE_URL.rstrip("/")
        headers = {
            "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}"
        }
        url = f"{user_module_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=8,
            )
        except requests.RequestException as exc:
            logger.error("Fallo al invocar user_module %s: %s", url, exc)
            raise ValidationError("No se pudo contactar al módulo de usuarios")

        if response.status_code >= 400:
            logger.error(
                "Error en módulo de usuarios: %s - %s",
                response.status_code,
                response.text,
            )
            return None

        try:
            return response.json()
        except ValueError:
            return None

    def _fetch_persona(
        self, persona_external: str, token: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene información de la persona desde el módulo de usuarios."""
        if not persona_external:
            return None
        try:
            response = self._call_user_module(
                "get", f"/api/person/search/{persona_external}", token
            )
            if not response:
                return None
            persona_data = response.get("data") if isinstance(response, dict) else None
            if persona_data:
                return {
                    "nombre": persona_data.get("first_name")
                    or persona_data.get("firts_name"),
                    "apellido": persona_data.get("last_name"),
                    "identificacion": persona_data.get("identification"),
                }
            return None
        except Exception:
            return None

    def _get_persona_info(self, atleta, token: str) -> Dict[str, Any]:
        """Obtiene información de la persona con fallback a datos locales."""
        persona_info = self._fetch_persona(atleta.persona_external, token)

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

    def get_atletas_habilitados_con_persona(
        self, token: str, user=None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene atletas con inscripción habilitada y sus datos de persona.

        REGLA DE NEGOCIO ACTUALIZADA:
        - Los ENTRENADORES pueden ver TODOS los atletas con inscripción habilitada.
        - La asignación a grupos es para organización, NO limita la visibilidad.
        - Esto permite registrar pruebas antropométricas a cualquier atleta inscrito.
        """
        queryset = Atleta.objects.filter(inscripcion__habilitada=True)

        # Los entrenadores ven TODOS los atletas con inscripción habilitada
        # Ya no se filtra por grupos asignados al entrenador
        if user and user.role == "ENTRENADOR":
            entrenador = Entrenador.objects.filter(persona_external=user.pk).first()
            if not entrenador:
                # Si el usuario no está registrado como entrenador, denegar acceso
                return []
            # Se mantiene el queryset sin filtro de grupos para máxima visibilidad

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
