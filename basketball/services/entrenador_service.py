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
        # Intenta extraer de 'data' si existe (formato común de respuesta)
        data = payload.get("data")
        if isinstance(data, dict):
            for key in (
                "external",
                "external_id",
                "external_person",
                "uuid",
                "id",
            ):
                value = data.get(key)
                if value:
                    return str(value)

        # Intenta extraer directamente del payload (formato de búsqueda según swagger)
        if isinstance(payload, dict):
            for key in (
                "external",
                "external_id",
                "external_person",
                "uuid",
                "id",
            ):
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

        especialidad = entrenador_data.get("especialidad")
        club_asignado = entrenador_data.get("club_asignado")
        if not especialidad or not club_asignado:
            raise ValidationError("especialidad y club_asignado son obligatorios")

        # Asegurar email y contraseña para save-account
        if not persona_data.get("email"):
            raise ValidationError("Email es obligatorio")

        if not persona_data.get("password"):
            raise ValidationError("Password es obligatorio")

        persona_response = None
        persona_external = None

        # Intentar crear con cuenta primero (más confiable en este entorno)
        try:
            # Usar save-account en lugar de save
            persona_response = self._call_user_module(
                "post", "/api/person/save-account", token, persona_data
            )
            # save-account retorna data vacía en éxito, así que DEBEMOS buscar
            persona_external = self._extract_external(persona_response)

            # Siempre buscar después de save-account porque podría no retornar el ID
            if not persona_external and persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                persona_external = (
                    self._extract_external(lookup_response) if lookup_response else None
                )

        except ValidationError as exc:
            message = str(exc)
            # Si ya está registrada, intentar encontrarla
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
                # Si save-account falló por otras razones, intentar buscar por si acaso
                # existe pero save-account falló por problemas de email/password.
                if persona_data.get("identification"):
                    lookup_response = self._search_by_identification(
                        persona_data.get("identification"), token
                    )
                    if lookup_response:
                        persona_external = self._extract_external(lookup_response)

                if not persona_external:
                    raise

        if not persona_external:
            # Fallback: intentar encontrar en la lista all_filter
            fallback_person = self._search_in_all_filter(
                persona_data.get("identification"), token
            )
            if fallback_person:
                persona_external = self._extract_external(fallback_person)

        if not persona_external:
            raise ValidationError("El módulo de usuarios no retornó external_id")

        if self.dao.exists(persona_external=persona_external):
            raise ValidationError(
                "Ya existe un entrenador con ese external"
            )

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
        if not entrenador:
            return None

        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        persona_data = persona_data.copy()
        persona_data.setdefault("external", entrenador.persona_external)

        # 1. Llamar al endpoint de actualización
        self._call_user_module("post", "/api/person/update", token, persona_data)

        # 2. Buscar de nuevo para obtener el external_id potencialmente nuevo
        # El endpoint de actualización retorna data vacía, así que debemos buscar por identificación
        ident = persona_data.get("identification")
        new_external = None

        if ident:
            lookup_response = self._search_by_identification(ident, token)
            new_external = (
                self._extract_external(lookup_response) if lookup_response else None
            )

        # Fallback si la búsqueda falló o no se proveyó identificación (poco probable)
        if not new_external:
            new_external = entrenador.persona_external

        if new_external != entrenador.persona_external and self.dao.exists(
            persona_external=new_external
        ):
            raise ValidationError("Ya existe otro entrenador con ese external")

        # Actualizar campos del entrenador
        update_data = {}
        if "especialidad" in entrenador_data:
            update_data["especialidad"] = entrenador_data["especialidad"]
        if "club_asignado" in entrenador_data:
            update_data["club_asignado"] = entrenador_data["club_asignado"]

        if update_data:
            self.dao.update(entrenador, **update_data)

        # Si cambió el external, actualizarlo
        if new_external != entrenador.persona_external:
            self.dao.update(entrenador, persona_external=new_external)

        # Refrescar el objeto
        entrenador.refresh_from_db()

        persona_info = self._fetch_persona(new_external, token, allow_fail=True)
        return self._build_response(entrenador, persona_info)

    def get_entrenador(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return None

        persona_info = self._fetch_persona(entrenador.persona_external, token, allow_fail=True)
        return self._build_response(entrenador, persona_info)

    def list_entrenadores(self, token: str) -> List[Dict[str, Any]]:
        entrenadores = self.dao.get_activos()
        result = []
        for entrenador in entrenadores:
            persona_info = self._fetch_persona(entrenador.persona_external, token, allow_fail=True)
            result.append(self._build_response(entrenador, persona_info))
        return result

    def delete_entrenador(self, pk: int) -> bool:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return False
        self.dao.delete(entrenador)
        return True
