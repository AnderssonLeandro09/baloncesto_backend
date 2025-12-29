"""
Servicio de negocio para Inscripciones.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import date

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from ..models import Inscripcion, Atleta
from ..dao.inscripcion_dao import InscripcionDAO
from ..dao.atleta_dao import AtletaDAO

logger = logging.getLogger(__name__)


class InscripcionService:
    """
    Lógica de negocio para la gestión de inscripciones.
    """

    def __init__(self):
        self.inscripcion_dao = InscripcionDAO()
        self.atleta_dao = AtletaDAO()
        self.user_module_url = settings.USER_MODULE_URL.rstrip("/")

    # ======================================================================
    # Helper HTTP
    # ======================================================================
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
            message = self._extract_message(response)
            raise ValidationError(f"Error en módulo de usuarios: {message}")

        try:
            return response.json()
        except ValueError:
            raise ValidationError("Respuesta inválida del módulo de usuarios")

    def _extract_message(self, response) -> str:
        try:
            data = response.json()
            return data.get("message") or str(data)
        except Exception:
            return response.text or "error"

    def _extract_external(self, response_data: Dict[str, Any]) -> Optional[str]:
        if not response_data:
            return None
        data = response_data.get("data")
        if isinstance(data, dict):
            return data.get("external_id") or data.get("external")
        return None

    def _search_by_identification(
        self, identification: Optional[str], token: str
    ) -> Optional[Dict[str, Any]]:
        if not identification:
            return None
        try:
            return self._call_user_module(
                "get",
                f"/api/person/search_identification/{identification}",
                token,
            )
        except Exception:
            return None

    def _fetch_persona(
        self, persona_external: str, token: str, allow_fail: bool = False
    ) -> Optional[Dict[str, Any]]:
        try:
            return self._call_user_module(
                "get", f"/api/person/search/{persona_external}", token
            )
        except Exception as exc:
            if allow_fail:
                return None
            raise ValidationError(f"No se pudo obtener datos de la persona: {exc}")

    def _build_response(
        self,
        atleta: Atleta,
        inscripcion: Inscripcion,
        persona_payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        persona_data = (
            persona_payload.get("data") if isinstance(persona_payload, dict) else None
        )
        return {
            "atleta": {
                "id": atleta.id,
                "persona_external": atleta.persona_external,
                "fecha_nacimiento": atleta.fecha_nacimiento,
                "edad": atleta.edad,
                "sexo": atleta.sexo,
                "telefono": atleta.telefono,
                "tipo_sangre": atleta.tipo_sangre,
                "alergias": atleta.alergias,
                "enfermedades": atleta.enfermedades,
                "medicamentos": atleta.medicamentos,
                "lesiones": atleta.lesiones,
                "nombre_representante": atleta.nombre_representante,
                "cedula_representante": atleta.cedula_representante,
                "parentesco_representante": atleta.parentesco_representante,
                "telefono_representante": atleta.telefono_representante,
                "correo_representante": atleta.correo_representante,
                "direccion_representante": atleta.direccion_representante,
                "ocupacion_representante": atleta.ocupacion_representante,
            },
            "inscripcion": {
                "id": inscripcion.id,
                "fecha_inscripcion": inscripcion.fecha_inscripcion,
                "tipo_inscripcion": inscripcion.tipo_inscripcion,
                "fecha_creacion": inscripcion.fecha_creacion,
                "habilitada": inscripcion.habilitada,
            },
            "persona": persona_data,
        }

    # ======================================================================
    # CRUD operations
    # ======================================================================
    def create_atleta_inscripcion(
        self,
        persona_data: Dict[str, Any],
        atleta_data: Dict[str, Any],
        inscripcion_data: Dict[str, Any],
        token: str,
    ) -> Dict[str, Any]:
        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        atleta_data = atleta_data or {}
        inscripcion_data = inscripcion_data or {}

        if not persona_data.get("email"):
            raise ValidationError("Email es obligatorio")
        if not persona_data.get("password"):
            raise ValidationError("Password es obligatorio")

        persona_external = None

        try:
            persona_response = self._call_user_module(
                "post", "/api/person/save-account", token, persona_data
            )
            persona_external = self._extract_external(persona_response)

            if not persona_external and persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                persona_external = (
                    self._extract_external(lookup_response) if lookup_response else None
                )

        except ValidationError as exc:
            message = str(exc)
            if (
                "ya esta registrada" in message.lower()
                or "already registered" in message.lower()
            ):
                persona_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                persona_external = (
                    self._extract_external(persona_response)
                    if persona_response
                    else None
                )
            else:
                raise

        if not persona_external:
            raise ValidationError("El módulo de usuarios no retornó external_id")

        if self.atleta_dao.exists(persona_external=persona_external):
            atleta = self.atleta_dao.get_by_filter(
                persona_external=persona_external
            ).first()
        else:
            atleta = self.atleta_dao.create(
                persona_external=persona_external, **atleta_data
            )

        inscripcion = self.inscripcion_dao.get_by_filter(atleta=atleta).first()
        if inscripcion:
            if not inscripcion.habilitada:
                inscripcion = self.inscripcion_dao.update(
                    inscripcion.id, habilitada=True
                )
        else:
            inscripcion_params = {
                "atleta": atleta,
                "fecha_inscripcion": date.today(),
                "tipo_inscripcion": "MAYOR_EDAD",
                "habilitada": True,
            }
            inscripcion_params.update(inscripcion_data)
            inscripcion = self.inscripcion_dao.create(**inscripcion_params)

        persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
        return self._build_response(atleta, inscripcion, persona_info)

    def update_atleta_inscripcion(
        self,
        inscripcion_id: int,
        persona_data: Dict[str, Any],
        atleta_data: Dict[str, Any],
        inscripcion_data: Dict[str, Any],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
        if not inscripcion:
            return None

        atleta = inscripcion.atleta

        if persona_data:
            persona_payload = persona_data.copy()
            persona_payload.setdefault("external", atleta.persona_external)
            self._call_user_module("post", "/api/person/update", token, persona_payload)

        if atleta_data:
            atleta = self.atleta_dao.update(atleta.id, **atleta_data)

        if inscripcion_data:
            inscripcion = self.inscripcion_dao.update(
                inscripcion.id, **inscripcion_data
            )

        persona_info = self._fetch_persona(
            atleta.persona_external, token, allow_fail=True
        )
        return self._build_response(atleta, inscripcion, persona_info)

    def get_inscripcion_completa(
        self, inscripcion_id: int, token: str
    ) -> Optional[Dict[str, Any]]:
        inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
        if not inscripcion:
            return None

        atleta = inscripcion.atleta
        persona_info = self._fetch_persona(
            atleta.persona_external, token, allow_fail=True
        )
        return self._build_response(atleta, inscripcion, persona_info)

    def list_inscripciones_completas(self, token: str) -> List[Dict[str, Any]]:
        inscripciones = self.inscripcion_dao.get_all()
        results = []
        for ins in inscripciones:
            atleta = ins.atleta
            persona_info = self._fetch_persona(
                atleta.persona_external, token, allow_fail=True
            )
            results.append(self._build_response(atleta, ins, persona_info))
        return results

    def cambiar_estado_inscripcion(self, inscripcion_id: int) -> Optional[Inscripcion]:
        """Alterna el estado de habilitación de una inscripción."""
        inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
        if not inscripcion:
            return None
        nuevo_estado = not inscripcion.habilitada
        return self.inscripcion_dao.update(inscripcion_id, habilitada=nuevo_estado)
