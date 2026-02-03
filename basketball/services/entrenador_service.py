"""Servicio de negocio para Entrenador."""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from ..constants import ErrorMessages
from ..dao.entrenador_dao import EntrenadorDAO
from ..models import Entrenador

logger = logging.getLogger(__name__)


class EntrenadorService:
    """Lógica de negocio para entrenadores."""

    def __init__(self):
        self.dao = EntrenadorDAO()
        self.user_module_url = settings.USER_MODULE_URL.rstrip("/")
        
        # En Linux, host.docker.internal no se resuelve, usar localhost
        if os.name != "nt" and "host.docker.internal" in self.user_module_url:
            self.user_module_url = self.user_module_url.replace("host.docker.internal", "localhost")

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
        """Extrae el external_id de la respuesta del módulo de usuarios.

        Busca en múltiples ubicaciones posibles y niveles para encontrar un ID válido.
        """
        if not payload or not isinstance(payload, dict):
            logger.warning(f"Payload inválido para extraer external: {payload}")
            return None

        # Campos posibles donde el ID puede estar
        possible_keys = (
            "external",
            "external_id",
            "external_person",
            "uuid",
            "id",
            "pk",
        )

        # 1. Buscar directamente en payload
        for key in possible_keys:
            value = payload.get(key)
            if value:
                logger.info(f"External encontrado en payload['{key}']: {value}")
                return str(value)

        # 2. Buscar dentro de payload["data"]
        data = payload.get("data")
        if isinstance(data, dict):
            for key in possible_keys:
                value = data.get(key)
                if value:
                    logger.info(
                        f"External encontrado en payload['data']['{key}']: {value}"
                    )
                    return str(value)

        # 3. Buscar dentro de payload["user"] (posible estructura alternativa)
        user = payload.get("user")
        if isinstance(user, dict):
            for key in possible_keys:
                value = user.get(key)
                if value:
                    logger.info(
                        f"External encontrado en payload['user']['{key}']: {value}"
                    )
                    return str(value)

        # 4. Buscar dentro de payload["persona"] (posible estructura alternativa)
        persona = payload.get("persona")
        if isinstance(persona, dict):
            for key in possible_keys:
                value = persona.get(key)
                if value:
                    logger.info(
                        f"External encontrado en payload['persona']['{key}']: {value}"
                    )
                    return str(value)

        # 5. Búsqueda recursiva en todos los valores del diccionario
        for key, value in payload.items():
            if isinstance(value, dict):
                # Si el valor es un diccionario, buscar recursivamente
                result = self._extract_external(value)
                if result:
                    logger.info(
                        f"External encontrado recursivamente en payload['{key}']: {result}"
                    )
                    return result

        logger.warning(f"No se pudo extraer external_id de la respuesta: {payload}")
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
    def _validate_persona_data(self, persona_data: Dict[str, Any]) -> None:
        """Valida que los datos de persona sean completos."""
        if not persona_data:
            raise ValidationError(ErrorMessages.ENTRENADOR_PERSONA_DATA_REQUIRED)

        if not persona_data.get("email"):
            raise ValidationError(ErrorMessages.ENTRENADOR_EMAIL_REQUIRED)

        if not persona_data.get("password"):
            raise ValidationError(ErrorMessages.ENTRENADOR_PASSWORD_REQUIRED)

    def _validate_entrenador_data(self, entrenador_data: Dict[str, Any]) -> None:
        """Valida que los datos del entrenador sean completos."""
        especialidad = entrenador_data.get("especialidad")
        club_asignado = entrenador_data.get("club_asignado")

        if not especialidad or not club_asignado:
            raise ValidationError(ErrorMessages.ENTRENADOR_ESPECIALIDAD_REQUIRED)

    def _get_or_create_persona_external(
        self,
        persona_data: Dict[str, Any],
        token: str,
    ) -> str:
        """Obtiene o crea el external_id de persona."""
        logger.info(
            f"Obteniendo o creando persona externa para identificación: {persona_data.get('identification')}"
        )

        # Intentar crear/registrar persona
        persona_external = self._try_create_persona(persona_data, token)

        # Si falla, buscar persona existente
        if not persona_external:
            logger.info(
                f"Buscando persona existente con identificación: {persona_data.get('identification')}"
            )
            persona_external = self._find_existing_persona(persona_data, token)

        if not persona_external:
            identification = persona_data.get("identification", "desconocida")
            error_msg = f"{ErrorMessages.ENTRENADOR_EXTERNAL_NOT_RETURNED}. Identificación: {identification}"
            logger.error(f"No se pudo obtener external_id: {error_msg}")
            raise ValidationError(error_msg)

        logger.info(f"External_id obtenido exitosamente: {persona_external}")
        return persona_external

    def _try_create_persona(
        self, persona_data: Dict[str, Any], token: str
    ) -> Optional[str]:
        """Intenta crear una persona en el módulo de usuarios."""
        try:
            logger.info(
                f"Intentando crear persona con identificación: {persona_data.get('identification')}"
            )
            persona_response = self._call_user_module(
                "post", "/api/person/save-account", token, persona_data
            )
            logger.info(f"Respuesta de save-account: {persona_response}")

            persona_external = self._extract_external(persona_response)

            # Si no obtuvimos external pero tenemos cédula, buscar por cédula
            if not persona_external and persona_data.get("identification"):
                logger.info(
                    f"No se encontró external en save-account, buscando por identificación: {persona_data.get('identification')}"
                )
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                if lookup_response:
                    logger.info(
                        f"Respuesta de búsqueda por identificación: {lookup_response}"
                    )
                    persona_external = self._extract_external(lookup_response)
                else:
                    logger.warning(
                        "No se obtuvo respuesta de búsqueda por identificación"
                    )

            if persona_external:
                logger.info(f"Persona externa obtenida: {persona_external}")
            else:
                logger.error(
                    f"No se pudo obtener external_id para persona con identificación: {persona_data.get('identification')}"
                )

            return persona_external
        except ValidationError as e:
            logger.error(f"Error de validación al crear persona: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al crear persona: {str(e)}")
            return None

    def _find_existing_persona(
        self, persona_data: Dict[str, Any], token: str
    ) -> Optional[str]:
        """Busca una persona existente por identificación."""
        identification = persona_data.get("identification")
        if not identification:
            logger.warning(
                "No se proporcionó identificación para buscar persona existente"
            )
            return None

        logger.info(f"Buscando persona por identificación: {identification}")

        # Buscar por cédula
        try:
            lookup_response = self._search_by_identification(identification, token)
            if lookup_response:
                logger.info(
                    f"Persona encontrada por búsqueda de identificación: {lookup_response}"
                )
                external = self._extract_external(lookup_response)
                if external:
                    return external
        except Exception as e:
            logger.warning(f"Error buscando por identificación: {str(e)}")

        # Buscar en todos los registros
        try:
            logger.info(
                f"Buscando en todos los registros para identificación: {identification}"
            )
            fallback_person = self._search_in_all_filter(identification, token)
            if fallback_person:
                logger.info(
                    f"Persona encontrada en todos los registros: {fallback_person}"
                )
                external = self._extract_external(fallback_person)
                if external:
                    return external
        except Exception as e:
            logger.warning(f"Error buscando en todos los registros: {str(e)}")

        logger.warning(f"No se encontró persona con identificación: {identification}")
        return None

    def _check_entrenador_exists(self, persona_external: str) -> None:
        """Verifica si ya existe un entrenador con ese external."""
        if self.dao.exists(persona_external=persona_external, eliminado=False):
            raise ValidationError(ErrorMessages.ENTRENADOR_ALREADY_EXISTS)

    def create_entrenador(
        self,
        persona_data: Dict[str, Any],
        entrenador_data: Dict[str, Any],
        token: str,
    ) -> Dict[str, Any]:
        """Crea un nuevo entrenador."""
        # Validaciones iniciales (guard clauses)
        self._validate_persona_data(persona_data)
        self._validate_entrenador_data(entrenador_data)

        # Obtener persona_external
        persona_external = self._get_or_create_persona_external(persona_data, token)

        # Verificar que no exista
        self._check_entrenador_exists(persona_external)

        # Crear entrenador
        entrenador = self.dao.create(
            persona_external=persona_external,
            especialidad=entrenador_data["especialidad"],
            club_asignado=entrenador_data["club_asignado"],
            eliminado=False,
        )

        # Obtener información de persona y construir respuesta
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
            raise ValidationError(ErrorMessages.ENTRENADOR_PERSONA_DATA_REQUIRED)

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
            raise ValidationError(ErrorMessages.ENTRENADOR_EXTERNAL_IN_USE)

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

    def get_entrenador(self, pk: int, token: str) -> Optional[Dict[str, Any]]:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador or entrenador.eliminado:
            return None
        persona_info = self._fetch_persona(
            entrenador.persona_external, token, allow_fail=True
        )
        return self._build_response(entrenador, persona_info)

    def list_entrenadores(self, token: str) -> List[Dict[str, Any]]:
        entrenadores = self.dao.get_by_filter(eliminado=False)
        resultados: List[Dict[str, Any]] = []
        for entrenador in entrenadores:
            persona_info = self._fetch_persona(
                entrenador.persona_external, token, allow_fail=True
            )
            resultados.append(self._build_response(entrenador, persona_info))
        return resultados
