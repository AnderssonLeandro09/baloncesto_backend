"""Servicio de negocio para Entrenador."""

import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from ..dao.entrenador_dao import EntrenadorDAO
from ..models import Entrenador

logger = logging.getLogger(__name__)


class EntrenadorService:
    """Lógica de negocio para entrenadores."""

    def __init__(self):
        self.dao = EntrenadorDAO()
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
            logger.error(f"Error del user_module con status {response.status_code}: {response.text}")
            logger.error(f"Mensaje extraído: {message}")
            # Pasar el mensaje tal cual, sin agregar prefijo
            raise ValidationError(message)


        try:
            return response.json()
        except ValueError:
            raise ValidationError("Respuesta inválida del módulo de usuarios")

    def _extract_message(self, response) -> str:
        try:
            data = response.json()
            # Intentar extraer mensaje de diferentes formatos
            if isinstance(data, dict):
                # Buscar mensaje en varias ubicaciones comunes
                msg = data.get("message") or data.get("error") or data.get("detail")
                if msg:
                    if isinstance(msg, list):
                        msg = " | ".join(str(m) for m in msg)
                    return str(msg)
                # Si hay errores de validación, concatenarlos
                if "errors" in data:
                    errors = data.get("errors", {})
                    if isinstance(errors, dict):
                        error_msgs = [f"{k}: {v}" for k, v in errors.items()]
                        return " | ".join(error_msgs)
                    elif isinstance(errors, list):
                        return " | ".join(str(e) for e in errors)
                # Buscar errores en la raíz del diccionario (formato DRF)
                for key, value in data.items():
                    if isinstance(value, (list, str)) and value and key != "non_field_errors":
                        if isinstance(value, list):
                            return f"{key}: " + " | ".join(str(v) for v in value)
                        else:
                            return f"{key}: {value}"
            return str(data)
        except Exception as e:
            logger.error(f"Error extrayendo mensaje de respuesta: {e}")
            return response.text or "error"

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

    def _search_in_all_filter(
        self, identification: str, token: str
    ) -> Optional[Dict[str, Any]]:
        try:
            response = self._call_user_module("get", "/api/person/all_filter", token)
            data = response.get("data")
            if isinstance(data, list):
                for person in data:
                    if (
                        isinstance(person, dict)
                        and person.get("identification") == identification
                    ):
                        return person
            return None
        except Exception:
            return None

    def _extract_external(self, payload: Dict[str, Any]) -> Optional[str]:
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("external", "external_id", "external_person", "uuid", "id"):
                value = data.get(key)
                if value:
                    return str(value)

        if isinstance(payload, dict):
            for key in ("external", "external_id", "external_person", "uuid", "id"):
                value = payload.get(key)
                if value:
                    return str(value)

        return None

    def _fetch_persona(
        self, external: str, token: str, allow_fail: bool = False
    ) -> Optional[Dict[str, Any]]:
        try:
            return self._call_user_module(
                "get", f"/api/person/search/{external}", token
            )
        except Exception:
            if allow_fail:
                return None
            raise

    def _build_response(
        self,
        entrenador: Entrenador,
        persona_payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        persona_data = (
            persona_payload.get("data") if isinstance(persona_payload, dict) else None
        )
        return {
            "entrenador": {
                "id": entrenador.id,
                "persona_external": entrenador.persona_external,
                "especialidad": entrenador.especialidad,
                "club_asignado": entrenador.club_asignado,
                "eliminado": entrenador.eliminado,
            },
            "persona": persona_data,
        }

    # ======================================================================
    # CRUD operations
    # ======================================================================
    def create_entrenador(
        self,
        persona_data: Dict[str, Any],
        entrenador_data: Dict[str, Any],
        token: str,
    ) -> Dict[str, Any]:
        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        # Debug logging detallado
        logger.info(f"=== CREANDO ENTRENADOR ===")
        logger.info(f"Persona data completa: {persona_data}")
        logger.info(f"Fields en persona_data:")
        for key, value in persona_data.items():
            logger.info(f"  {key}: {value!r} (tipo: {type(value).__name__})")

        especialidad = entrenador_data.get("especialidad")
        club_asignado = entrenador_data.get("club_asignado")
        if not especialidad or not club_asignado:
            raise ValidationError("especialidad y club_asignado son obligatorios")

        email = persona_data.get("email")
        if not email:
            raise ValidationError("Email es obligatorio")

        if not persona_data.get("password"):
            raise ValidationError("Password es obligatorio")

        persona_response = None
        persona_external = None

        try:
            logger.info(f"Llamando a user_module para crear persona")
            persona_response = self._call_user_module(
                "post", "/api/person/save-account", token, persona_data
            )
            logger.info(f"Respuesta del user_module: {persona_response}")
            persona_external = self._extract_external(persona_response)

            if not persona_external and persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                persona_external = (
                    self._extract_external(lookup_response) if lookup_response else None
                )

        except ValidationError as exc:
            logger.error(f"Error de validación al crear persona: {exc}")
            if persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                if lookup_response:
                    persona_external = self._extract_external(lookup_response)

            if not persona_external:
                fallback_person = self._search_in_all_filter(
                    persona_data.get("identification"), token
                )
                if fallback_person:
                    persona_external = self._extract_external(fallback_person)

            if not persona_external:
                raise exc

        if not persona_external:
            raise ValidationError("El módulo de usuarios no retornó external_id")

        if self.dao.exists(persona_external=persona_external, eliminado=False):
            raise ValidationError("Ya existe un entrenador con ese external")

        entrenador = self.dao.create(
            persona_external=persona_external,
            especialidad=especialidad,
            club_asignado=club_asignado,
            eliminado=False,
        )

        persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
        return self._build_response(entrenador, persona_info)

    def update_entrenador(
        self,
        pk: int,
        persona_data: Dict[str, Any],
        entrenador_data: Dict[str, Any],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador or entrenador.eliminado:
            return None

        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        persona_data = persona_data.copy()
        persona_data.setdefault("external", entrenador.persona_external)

        self._call_user_module("post", "/api/person/update", token, persona_data)

        ident = persona_data.get("identification")
        new_external = None

        if ident:
            lookup_response = self._search_by_identification(ident, token)
            new_external = (
                self._extract_external(lookup_response) if lookup_response else None
            )

        if not new_external:
            new_external = entrenador.persona_external

        if new_external != entrenador.persona_external and self.dao.exists(
            persona_external=new_external, eliminado=False
        ):
            raise ValidationError(
                "El external_id retornado ya está en uso por otro entrenador"
            )

        especialidad = entrenador_data.get("especialidad", entrenador.especialidad)
        club_asignado = entrenador_data.get("club_asignado", entrenador.club_asignado)

        updated = self.dao.update(
            pk,
            persona_external=new_external,
            especialidad=especialidad,
            club_asignado=club_asignado,
            eliminado=False,
        )

        if not updated:
            return None

        persona_info = self._fetch_persona(new_external, token, allow_fail=True)
        return self._build_response(updated, persona_info)

    def delete_entrenador(self, pk: int) -> bool:
        updated = self.dao.update(pk, eliminado=True)
        return updated is not None

    def toggle_estado(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return None

        nuevo_estado = not entrenador.eliminado
        updated = self.dao.update(pk, eliminado=nuevo_estado)
        if not updated:
            return None

        persona_info = self._fetch_persona(
            updated.persona_external, token, allow_fail=True
        )
        return self._build_response(updated, persona_info)

    def get_entrenador(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador or entrenador.eliminado:
            return None
        persona_info = self._fetch_persona(
            entrenador.persona_external, token, allow_fail=True
        )
        return self._build_response(entrenador, persona_info)

    def list_entrenadores(self, token: str) -> List[Dict[str, Any]]:
        entrenadores = self.dao.get_by_filter()
        resultados: List[Dict[str, Any]] = []
        for entrenador in entrenadores:
            persona_info = self._fetch_persona(
                entrenador.persona_external, token, allow_fail=True
            )
            resultados.append(self._build_response(entrenador, persona_info))
        return resultados
