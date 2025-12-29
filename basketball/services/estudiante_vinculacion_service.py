"""Servicio de negocio para Estudiante de Vinculación."""

import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from ..dao.estudiante_vinculacion_dao import EstudianteVinculacionDAO
from ..models import EstudianteVinculacion

logger = logging.getLogger(__name__)


class EstudianteVinculacionService:
    """Lógica de negocio para estudiantes de vinculación."""

    def __init__(self):
        self.dao = EstudianteVinculacionDAO()
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
        self,
        estudiante: EstudianteVinculacion,
        persona_payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        persona_data = (
            persona_payload.get("data") if isinstance(persona_payload, dict) else None
        )
        return {
            "estudiante": {
                "id": estudiante.id,
                "persona_external": estudiante.persona_external,
                "carrera": estudiante.carrera,
                "semestre": estudiante.semestre,
                "eliminado": estudiante.eliminado,
            },
            "persona": persona_data,
        }

    # ======================================================================
    # CRUD operations
    # ======================================================================
    def create_estudiante(
        self, persona_data: Dict[str, Any], estudiante_data: Dict[str, Any], token: str
    ) -> Dict[str, Any]:
        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        carrera = estudiante_data.get("carrera")
        semestre = estudiante_data.get("semestre")
        if not carrera or not semestre:
            raise ValidationError("carrera y semestre son obligatorios")

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

        if self.dao.exists(persona_external=persona_external, eliminado=False):
            raise ValidationError(
                "Ya existe un estudiante de vinculación con ese external"
            )

        estudiante = self.dao.create(
            persona_external=persona_external,
            carrera=carrera,
            semestre=semestre,
            eliminado=False,
        )

        persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
        return self._build_response(estudiante, persona_info)

    def update_estudiante(
        self,
        pk: int,
        persona_data: Dict[str, Any],
        estudiante_data: Dict[str, Any],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        estudiante = self.dao.get_by_id(pk)
        if not estudiante or estudiante.eliminado:
            return None

        if not persona_data:
            raise ValidationError("Datos de persona son obligatorios")

        persona_data = persona_data.copy()
        persona_data.setdefault("external", estudiante.persona_external)

        # 1. Llamar al endpoint de actualización
        self._call_user_module("post", "/api/person/update", token, persona_data)

        # 2. Buscar de nuevo para obtener el external_id potencialmente nuevo
        # El endpoint de actualización retorna data vacía, así que debemos buscar por identificación # noqa: E501
        ident = persona_data.get("identification")
        new_external = None

        if ident:
            lookup_response = self._search_by_identification(ident, token)
            new_external = (
                self._extract_external(lookup_response) if lookup_response else None
            )

        # Fallback si la búsqueda falló o no se proveyó identificación (poco probable)
        if not new_external:
            new_external = estudiante.persona_external

        if new_external != estudiante.persona_external and self.dao.exists(
            persona_external=new_external, eliminado=False
        ):
            raise ValidationError(
                "El external_id retornado ya está en uso por otro estudiante"
            )

        carrera = estudiante_data.get("carrera", estudiante.carrera)
        semestre = estudiante_data.get("semestre", estudiante.semestre)

        updated = self.dao.update(
            pk,
            persona_external=new_external,
            carrera=carrera,
            semestre=semestre,
            eliminado=False,
        )

        if not updated:
            return None

        persona_info = self._fetch_persona(new_external, token, allow_fail=True)
        return self._build_response(updated, persona_info)

    def delete_estudiante(self, pk: int) -> bool:
        updated = self.dao.update(pk, eliminado=True)
        return updated is not None

    def get_estudiante(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        estudiante = self.dao.get_by_id(pk)
        if not estudiante or estudiante.eliminado:
            return None
        persona_info = self._fetch_persona(
            estudiante.persona_external, token, allow_fail=True
        )
        return self._build_response(estudiante, persona_info)

    def list_estudiantes(self, token: str) -> List[Dict[str, Any]]:
        estudiantes = self.dao.get_by_filter(eliminado=False)
        resultados: List[Dict[str, Any]] = []
        for estudiante in estudiantes:
            persona_info = self._fetch_persona(
                estudiante.persona_external, token, allow_fail=True
            )
            resultados.append(self._build_response(estudiante, persona_info))
        return resultados
