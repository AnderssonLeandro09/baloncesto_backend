"""Servicio de negocio para Administrador."""

import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from ..dao.administrador_dao import AdministradorDAO
from ..models import Administrador

logger = logging.getLogger(__name__)


class AdministradorService:
    """Lógica de negocio para administradores."""

    def __init__(self):
        self.dao = AdministradorDAO()
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
                method=method, url=url, headers=headers, json=payload, timeout=8
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
                "get", f"/api/person/search_identification/{identification}", token
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
            for key in ("external", "external_id", "external_person", "uuid", "id"):
                value = data.get(key)
                if value:
                    return str(value)

        # Intenta extraer directamente del payload (formato de búsqueda según swagger)
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
        self, administrador: Administrador, persona_payload: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        persona_data = (
            persona_payload.get("data") if isinstance(persona_payload, dict) else None
        )
        return {
            "administrador": {
                "id": administrador.id,
                "persona_external": administrador.persona_external,
                "cargo": administrador.cargo,
                "estado": administrador.estado,
            },
            "persona": persona_data,
        }

    # ======================================================================
    # CRUD operations
    # ======================================================================
    def create_administrador(
        self,
        persona_data: Dict[str, Any],
        administrador_data: Dict[str, Any],
        token: str,
    ) -> Dict[str, Any]:
        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        cargo = administrador_data.get("cargo")
        # cargo es opcional en el modelo, pero si se requiere validación extra, agregar aquí. # noqa: E501

        # Validar que email y contraseña estén presentes
        if not persona_data.get("email"):
            raise ValidationError("El correo electrónico es obligatorio")

        if not persona_data.get("password"):
            raise ValidationError("La contraseña es obligatoria")

        persona_response = None
        persona_external = None

        # Intentar crear con cuenta primero
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
            # Intentar recuperar si la persona ya existe, independientemente del error
            # Esto cubre casos donde el mensaje de error no es estándar o es un error de BD (ej. Duplicate entry) # noqa: E501
            if persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                if lookup_response:
                    persona_external = self._extract_external(lookup_response)

            if not persona_external:
                # Fallback: intentar encontrar en la lista all_filter
                fallback_person = self._search_in_all_filter(
                    persona_data.get("identification"), token
                )
                if fallback_person:
                    persona_external = self._extract_external(fallback_person)

            if not persona_external:
                # Si realmente no pudimos encontrarla, lanzamos el error original
                raise exc

        if not persona_external:
            raise ValidationError("El módulo de usuarios no retornó external_id")

        if self.dao.exists(persona_external=persona_external, estado=True):
            raise ValidationError("Ya existe un administrador con ese external")

        administrador = self.dao.create(
            persona_external=persona_external,
            cargo=cargo,
            estado=True,
        )

        persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
        return self._build_response(administrador, persona_info)

    def update_administrador(
        self,
        pk: int,
        persona_data: Dict[str, Any],
        administrador_data: Dict[str, Any],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        administrador = self.dao.get_by_id(pk)
        if not administrador or not administrador.estado:
            return None

        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        persona_data = persona_data.copy()
        persona_data.setdefault("external", administrador.persona_external)

        # 1. Llamar al endpoint de actualización
        self._call_user_module("post", "/api/person/update", token, persona_data)

        # 2. Buscar de nuevo para obtener el external_id potencialmente nuevo
        ident = persona_data.get("identification")
        new_external = None

        if ident:
            lookup_response = self._search_by_identification(ident, token)
            new_external = (
                self._extract_external(lookup_response) if lookup_response else None
            )

        if not new_external:
            new_external = administrador.persona_external

        if new_external != administrador.persona_external and self.dao.exists(
            persona_external=new_external, estado=True
        ):
            raise ValidationError(
                "El external_id retornado ya está en uso por otro administrador"
            )

        cargo = administrador_data.get("cargo", administrador.cargo)

        updated = self.dao.update(
            pk,
            persona_external=new_external,
            cargo=cargo,
            estado=True,
        )

        if not updated:
            return None

        persona_info = self._fetch_persona(new_external, token, allow_fail=True)
        return self._build_response(updated, persona_info)

    def delete_administrador(self, pk: int) -> bool:
        administrador = self.dao.update(pk, estado=False)
        return administrador is not None

    def get_administrador_by_id(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        administrador = self.dao.get_by_id(pk)
        if not administrador or not administrador.estado:
            return None
        persona_info = self._fetch_persona(
            administrador.persona_external, token, allow_fail=True
        )
        return self._build_response(administrador, persona_info)

    def get_all_administradores(self, token: str) -> List[Dict[str, Any]]:
        administradores = self.dao.get_by_filter(estado=True)
        resultados: List[Dict[str, Any]] = []
        for admin in administradores:
            persona_info = self._fetch_persona(
                admin.persona_external, token, allow_fail=True
            )
            resultados.append(self._build_response(admin, persona_info))
        return resultados

    def get_by_persona_external(self, persona_external: str) -> Optional[Administrador]:
        return self.dao.get_by_persona_external(persona_external)
