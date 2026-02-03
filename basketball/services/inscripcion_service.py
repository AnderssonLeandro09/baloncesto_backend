"""
Servicio de negocio para Inscripciones.
CORREGIDO: Eliminada obligatoriedad de email/password según diagrama de clases.
MODO FAIL-SAFE: El sistema continúa funcionando aunque el microservicio de usuarios falle.

Refactorizado para cumplir con Quality Gate de SonarQube:
- Complejidad cognitiva reducida mediante extracción de métodos
- Mapeo robusto centralizado en _normalize_atleta_data()
- Constantes para mensajes de error
"""

import logging
import re
import secrets
import string
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

from ..dao.atleta_dao import AtletaDAO
from ..dao.inscripcion_dao import InscripcionDAO
from ..models import Atleta, Inscripcion

logger = logging.getLogger(__name__)


# ==========================================================================
# CONSTANTES DE MENSAJES DE ERROR
# ==========================================================================
class ErrorMessages:
    """Mensajes de error centralizados para evitar duplicación de literales."""

    PERSONA_DATA_REQUIRED = "Datos de persona son requeridos"
    NOMBRE_REQUIRED = "El nombre del atleta es requerido"
    NOMBRE_INVALID = "El nombre solo puede contener letras y espacios"
    APELLIDO_REQUIRED = "El apellido del atleta es requerido"
    APELLIDO_INVALID = "El apellido solo puede contener letras y espacios"
    CEDULA_REQUIRED = "La cédula es obligatoria para el registro"
    CEDULA_INVALID = "La cédula debe tener exactamente 10 dígitos numéricos"
    TELEFONO_INVALID = "El teléfono debe tener exactamente 10 dígitos numéricos"
    INSCRIPCION_DUPLICADA = (
        "Este atleta ya tiene una inscripción activa. "
        "Verifica el número de cédula o contacta al administrador."
    )
    INSCRIPCION_NOT_FOUND = "Inscripción no encontrada"
    ENTRENADOR_NOT_FOUND = "Entrenador no encontrado"
    ERROR_INTERNO_GUARDAR = "Error interno al guardar"
    ERROR_ACTUALIZAR = "Error al actualizar"


# ==========================================================================
# CONSTANTES DE CONFIGURACIÓN
# ==========================================================================
CEDULA_LENGTH = 10
TELEFONO_LENGTH = 10
PASSWORD_LENGTH = 16
NOMBRE_PATTERN = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"


@dataclass
class NormalizedAtletaData:
    """Datos de atleta normalizados desde el frontend."""

    cedula: str
    nombre: str
    apellido: str
    telefono: str
    direccion: str
    email: str
    genero: str


class InscripcionService:
    """
    Servicio de lógica de negocio para la gestión de inscripciones de atletas.

    Responsabilidades:
    - Crear inscripciones con validación de duplicados
    - Actualizar datos de atleta/persona/inscripción
    - Gestionar estados de inscripción (habilitar/deshabilitar)
    - Comunicación con microservicio de usuarios (modo fail-safe)

    Características de resiliencia:
    - Modo offline: genera IDs locales si el microservicio falla
    - Datos locales: siempre persiste información en BD local
    - Mapeo robusto: soporta múltiples nombres de campo del frontend
    """

    def __init__(self):
        self.inscripcion_dao = InscripcionDAO()
        self.atleta_dao = AtletaDAO()
        self.user_module_url = (settings.USER_MODULE_URL or "").rstrip("/")

    # ======================================================================
    # MÉTODOS PRIVADOS - NORMALIZACIÓN DE DATOS (DRY)
    # ======================================================================
    def _normalize_atleta_data(self, raw_data: Dict[str, Any]) -> NormalizedAtletaData:
        """
        Centraliza el mapeo robusto de datos del frontend a la BD local.

        Soporta múltiples nombres de campo para evitar errores por typos
        o inconsistencias del frontend.

        Args:
            raw_data: Diccionario con datos crudos del frontend

        Returns:
            NormalizedAtletaData con campos normalizados
        """
        cedula = (
            raw_data.get("identification")
            or raw_data.get("cedula")
            or raw_data.get("dni")
            or ""
        )
        nombre = (
            raw_data.get("first_name")
            or raw_data.get("firts_name")  # Typo común del frontend
            or raw_data.get("nombres")
            or raw_data.get("nombre")
            or ""
        )
        apellido = (
            raw_data.get("last_name")
            or raw_data.get("apellidos")
            or raw_data.get("apellido")
            or ""
        )
        telefono = (
            raw_data.get("phono")
            or raw_data.get("telefono")
            or raw_data.get("phone")
            or raw_data.get("celular")
            or ""
        )
        direccion = (
            raw_data.get("direction")
            or raw_data.get("direccion")
            or raw_data.get("address")
            or ""
        )
        email = raw_data.get("email") or raw_data.get("correo") or ""
        genero = (
            raw_data.get("gender")
            or raw_data.get("genero")
            or raw_data.get("sexo")
            or ""
        )

        return NormalizedAtletaData(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            email=email,
            genero=genero,
        )

    def _extract_local_update_fields(
        self, normalized: NormalizedAtletaData
    ) -> Dict[str, Any]:
        """
        Construye diccionario de actualización local desde datos normalizados.

        Args:
            normalized: Datos normalizados del atleta

        Returns:
            Dict con campos no vacíos para actualización
        """
        local_update = {}
        if normalized.nombre:
            local_update["nombres"] = normalized.nombre
        if normalized.apellido:
            local_update["apellidos"] = normalized.apellido
        if normalized.cedula:
            local_update["cedula"] = normalized.cedula
        if normalized.email:
            local_update["email"] = normalized.email
        if normalized.telefono:
            local_update["telefono"] = normalized.telefono
        if normalized.direccion:
            local_update["direccion"] = normalized.direccion
        if normalized.genero:
            local_update["genero"] = normalized.genero
        return local_update

    # ======================================================================
    # MÉTODOS PRIVADOS - VALIDACIÓN (Complejidad reducida)
    # ======================================================================
    def _validate_creation_rules(self, normalized: NormalizedAtletaData) -> None:
        """
        Valida las reglas de negocio para la creación de inscripciones.

        Args:
            normalized: Datos normalizados del atleta

        Raises:
            ValidationError: Si alguna validación falla
        """
        self._validate_nombre(normalized.nombre)
        self._validate_apellido(normalized.apellido)
        self._validate_cedula(normalized.cedula)
        self._validate_telefono(normalized.telefono)

    def _validate_nombre(self, nombre: str) -> None:
        """Valida el campo nombre."""
        if not nombre or not nombre.strip():
            raise ValidationError(ErrorMessages.NOMBRE_REQUIRED)
        if not re.match(NOMBRE_PATTERN, nombre.strip()):
            raise ValidationError(ErrorMessages.NOMBRE_INVALID)

    def _validate_apellido(self, apellido: str) -> None:
        """Valida el campo apellido."""
        if not apellido or not apellido.strip():
            raise ValidationError(ErrorMessages.APELLIDO_REQUIRED)
        if not re.match(NOMBRE_PATTERN, apellido.strip()):
            raise ValidationError(ErrorMessages.APELLIDO_INVALID)

    def _validate_cedula(self, cedula: str) -> None:
        """Valida el campo cédula."""
        if not cedula or not cedula.strip():
            raise ValidationError(ErrorMessages.CEDULA_REQUIRED)
        cedula_limpia = self._clean_numeric_field(cedula)
        if len(cedula_limpia) != CEDULA_LENGTH or not cedula_limpia.isdigit():
            raise ValidationError(ErrorMessages.CEDULA_INVALID)

    def _validate_telefono(self, telefono: str) -> None:
        """Valida el campo teléfono si está presente."""
        if not telefono:
            return
        telefono_limpio = self._clean_numeric_field(telefono)
        if telefono_limpio and (
            len(telefono_limpio) != TELEFONO_LENGTH or not telefono_limpio.isdigit()
        ):
            raise ValidationError(ErrorMessages.TELEFONO_INVALID)

    def _clean_numeric_field(self, value: str) -> str:
        """Limpia un campo numérico de guiones y espacios."""
        return value.strip().replace("-", "").replace(" ", "")

    def _check_duplicate_inscripcion(self, cedula: str) -> None:
        """
        Verifica si existe una inscripción activa con la cédula dada.

        Args:
            cedula: Cédula a verificar

        Raises:
            ValidationError: Si ya existe inscripción activa
        """
        if not cedula:
            return

        atleta_existente = self.atleta_dao.get_by_filter(cedula=cedula).first()
        if not atleta_existente:
            return

        inscripcion_activa = self.inscripcion_dao.get_by_filter(
            atleta=atleta_existente, habilitada=True
        ).first()

        if inscripcion_activa:
            logger.warning(
                f"[DUPLICADO] Atleta con cédula {cedula} ya tiene "
                f"inscripción activa ID={inscripcion_activa.id}"
            )
            raise ValidationError(ErrorMessages.INSCRIPCION_DUPLICADA)

    # ======================================================================
    # MÉTODOS PRIVADOS - GENERACIÓN DE CREDENCIALES FAIL-SAFE
    # ======================================================================
    def _generate_failsafe_credentials(
        self, cedula: str, persona_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Genera credenciales dummy si no vienen del frontend.

        Args:
            cedula: Cédula del atleta
            persona_data: Datos de persona (se modifica in-place)

        Returns:
            Tuple con (email, persona_data actualizado)
        """
        email = persona_data.get("email") or persona_data.get("correo") or ""

        if not email:
            email = f"atleta_{cedula}_{int(time.time())}@local.system"
            logger.info(f"[FAIL-SAFE] Email dummy generado: {email}")

        if not persona_data.get("password"):
            alphabet = string.ascii_letters + string.digits + "!@#$%&*"
            persona_data["password"] = "".join(
                secrets.choice(alphabet) for _ in range(PASSWORD_LENGTH)
            )

        persona_data["email"] = email
        return email, persona_data

    # ======================================================================
    # MÉTODOS PRIVADOS - SINCRONIZACIÓN CON SERVICIO EXTERNO
    # ======================================================================
    def _sync_external_service(
        self, persona_data: Dict[str, Any], cedula: str, token: str
    ) -> str:
        """
        Sincroniza con el microservicio de usuarios (modo fail-safe).

        Args:
            persona_data: Datos de persona
            cedula: Cédula del atleta
            token: Token de autenticación

        Returns:
            ID externo del persona (o ID local si falla)
        """
        persona_external = None

        try:
            persona_response = self._call_user_module(
                "post",
                "/api/person/save-account",
                token,
                persona_data,
            )
            persona_external = self._extract_external(persona_response)

            if not persona_external and cedula:
                lookup_response = self._search_by_identification(cedula, token)
                persona_external = self._extract_external(lookup_response)
        except Exception as ext_err:
            logger.warning(f"[MODO OFFLINE] Error con microservicio externo: {ext_err}")
            persona_external = self._fallback_lookup(cedula, token)

        if not persona_external:
            persona_external = f"local_{cedula or 'unknown'}_{int(time.time())}"
            logger.info(f"[MODO OFFLINE] ID local generado: {persona_external}")

        return persona_external

    def _fallback_lookup(self, cedula: str, token: str) -> Optional[str]:
        """Intenta búsqueda silenciosa por cédula."""
        try:
            if cedula:
                lookup_response = self._search_by_identification(cedula, token)
                return self._extract_external(lookup_response)
        except Exception:
            pass
        return None

    # ======================================================================
    # MÉTODOS PRIVADOS - PERSISTENCIA LOCAL
    # ======================================================================
    def _persist_local_atleta(
        self,
        normalized: NormalizedAtletaData,
        email: str,
        persona_external: str,
        atleta_data: Optional[Dict[str, Any]],
    ) -> Atleta:
        """
        Crea o actualiza el atleta en la BD local.

        Args:
            normalized: Datos normalizados
            email: Email (puede ser generado)
            persona_external: ID externo de persona
            atleta_data: Datos adicionales del atleta

        Returns:
            Instancia de Atleta creada o actualizada
        """
        datos_atleta_local = {
            "nombres": normalized.nombre,
            "apellidos": normalized.apellido,
            "cedula": normalized.cedula,
            "email": email,
            "telefono": normalized.telefono,
            "direccion": normalized.direccion,
            "genero": normalized.genero,
        }

        valid_fields = [f.name for f in Atleta._meta.get_fields()]
        for key, value in (atleta_data or {}).items():
            if key in valid_fields and value is not None:
                datos_atleta_local[key] = value

        atleta = self._find_existing_atleta(persona_external, normalized.cedula)

        if atleta:
            return self._update_existing_atleta(
                atleta, datos_atleta_local, persona_external, valid_fields
            )
        return self._create_new_atleta(
            datos_atleta_local, persona_external, valid_fields
        )

    def _find_existing_atleta(
        self, persona_external: str, cedula: str
    ) -> Optional[Atleta]:
        """Busca atleta existente por persona_external o cédula."""
        atleta_por_external = self.atleta_dao.get_by_filter(
            persona_external=persona_external
        ).first()
        atleta_por_cedula = (
            self.atleta_dao.get_by_filter(cedula=cedula).first() if cedula else None
        )
        return atleta_por_external or atleta_por_cedula

    def _update_existing_atleta(
        self,
        atleta: Atleta,
        datos: Dict[str, Any],
        persona_external: str,
        valid_fields: List[str],
    ) -> Atleta:
        """Actualiza un atleta existente."""
        logger.info(f"[UPDATE] Actualizando atleta ID={atleta.id}")
        clean_data = {k: v for k, v in datos.items() if k in valid_fields and v}

        if not atleta.persona_external or atleta.persona_external.startswith("local_"):
            clean_data["persona_external"] = persona_external

        self.atleta_dao.update(atleta.id, **clean_data)
        return self.atleta_dao.get_by_id(atleta.id)

    def _create_new_atleta(
        self, datos: Dict[str, Any], persona_external: str, valid_fields: List[str]
    ) -> Atleta:
        """Crea un nuevo atleta."""
        cedula = datos.get("cedula", "unknown")
        logger.info(f"[CREATE] Creando nuevo atleta con cédula={cedula}")
        clean_data = {k: v for k, v in datos.items() if k in valid_fields and v}
        return self.atleta_dao.create(persona_external=persona_external, **clean_data)

    def _persist_local_inscripcion(
        self, atleta: Atleta, inscripcion_data: Dict[str, Any]
    ) -> Inscripcion:
        """
        Crea o reactiva la inscripción del atleta.

        Args:
            atleta: Instancia del atleta
            inscripcion_data: Datos de inscripción

        Returns:
            Instancia de Inscripción
        """
        inscripcion = self.inscripcion_dao.get_by_filter(atleta=atleta).first()

        if inscripcion:
            return self._reactivate_inscripcion(inscripcion, inscripcion_data)
        return self._create_new_inscripcion(atleta, inscripcion_data)

    def _reactivate_inscripcion(
        self, inscripcion: Inscripcion, inscripcion_data: Dict[str, Any]
    ) -> Inscripcion:
        """Reactiva una inscripción existente."""
        logger.info(f"[REACTIVAR] Inscripción existente ID={inscripcion.id}")
        update_data = {"habilitada": True}
        if inscripcion_data:
            update_data.update(inscripcion_data)
        self.inscripcion_dao.update(inscripcion.id, **update_data)
        return self.inscripcion_dao.get_by_id(inscripcion.id)

    def _create_new_inscripcion(
        self, atleta: Atleta, inscripcion_data: Dict[str, Any]
    ) -> Inscripcion:
        """Crea una nueva inscripción."""
        logger.info(f"[CREATE] Creando nueva inscripción para atleta ID={atleta.id}")
        inscripcion_params = {
            "atleta": atleta,
            "fecha_inscripcion": date.today(),
            "tipo_inscripcion": inscripcion_data.get("tipo_inscripcion", "MAYOR_EDAD"),
            "habilitada": True,
        }

        valid_insc_fields = [f.name for f in Inscripcion._meta.get_fields()]
        for key, value in inscripcion_data.items():
            if key in valid_insc_fields and key not in inscripcion_params:
                inscripcion_params[key] = value

        return self.inscripcion_dao.create(**inscripcion_params)

    # ======================================================================
    # Helper HTTP
    # ======================================================================
    def _build_auth_header(self, token: Optional[str]) -> Dict[str, str]:
        """Construye el header de autorización."""
        if not token:
            return {}
        bearer = token if token.startswith("Bearer ") else f"Bearer {token}"
        return {"Authorization": bearer}

    def _call_user_module(
        self,
        method: str,
        path: str,
        token: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Llamada al microservicio de usuarios con MODO OFFLINE.
        Si la conexión falla, retorna un dict vacío en lugar de lanzar excepción.
        """
        if not self.user_module_url:
            logger.warning("USER_MODULE_URL no configurado. Usando modo Dummy/Offline.")
            return {"data": {"external_id": f"offline_{int(time.time())}"}}

        headers = self._build_auth_header(token)
        url = f"{self.user_module_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=payload,
                timeout=10,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.warning(
                f"[MODO OFFLINE] Microservicio de usuarios no disponible: {url}"
            )
            logger.debug(f"Detalle conexión: {exc}")
            return {
                "offline": True,
                "data": {"external_id": f"offline_{int(time.time())}"},
            }
        except requests.exceptions.Timeout:
            logger.warning(f"[TIMEOUT] El microservicio tardó demasiado: {url}")
            return {
                "timeout": True,
                "data": {"external_id": f"timeout_{int(time.time())}"},
            }
        except requests.RequestException as exc:
            logger.error(f"[ERROR CONEXIÓN] Fallo inesperado user_module {url}: {exc}")
            return {}

        if response.status_code >= 400:
            message = self._extract_message(response)
            if (
                "ya existe" not in str(message).lower()
                and "already" not in str(message).lower()
            ):
                logger.warning(
                    f"Error externo no fatal ({response.status_code}): {message}"
                )

        try:
            return response.json()
        except ValueError:
            return {}

    def _extract_message(self, response) -> str:
        """Extrae mensaje de error de una respuesta HTTP."""
        try:
            data = response.json()
            return data.get("message") or str(data)
        except Exception:
            return response.text or "error desconocido"

    def _extract_external(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extrae el ID externo de una respuesta."""
        if not response_data:
            return None
        data = response_data.get("data")
        if isinstance(data, dict):
            return data.get("external_id") or data.get("external") or data.get("id")
        if isinstance(response_data, dict):
            return response_data.get("external_id")
        return None

    def _search_by_identification(
        self, identification: Optional[str], token: str
    ) -> Optional[Dict[str, Any]]:
        """Busca persona por identificación en el microservicio."""
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
        self,
        persona_external: str,
        token: str,
        allow_fail: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Obtiene datos de persona desde el microservicio."""
        try:
            return self._call_user_module(
                "get", f"/api/person/search/{persona_external}", token
            )
        except Exception:
            return {}

    def _build_response(
        self,
        atleta: Atleta,
        inscripcion: Inscripcion,
        persona_payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Construye la respuesta combinando datos locales y externos.
        PRIORIDAD: Datos locales del atleta (nunca se pierden).
        """
        persona_externa = (
            persona_payload.get("data") if isinstance(persona_payload, dict) else {}
        ) or {}

        persona_response = {
            "first_name": atleta.nombres or persona_externa.get("first_name", ""),
            "last_name": atleta.apellidos or persona_externa.get("last_name", ""),
            "identification": atleta.cedula
            or persona_externa.get("identification", ""),
            "email": atleta.email or persona_externa.get("email", ""),
            "phono": atleta.telefono or persona_externa.get("phono", ""),
            "direction": atleta.direccion or persona_externa.get("direction", ""),
            "gender": atleta.genero or atleta.sexo or persona_externa.get("gender", ""),
        }

        return {
            "atleta": {
                "id": atleta.id,
                "persona_external": atleta.persona_external,
                "nombres": atleta.nombres,
                "apellidos": atleta.apellidos,
                "cedula": atleta.cedula,
                "email": atleta.email,
                "direccion": atleta.direccion,
                "genero": atleta.genero,
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
            "persona": persona_response,
        }

    # ======================================================================
    # CRUD operations
    # ======================================================================
    def create_atleta_inscripcion(
        self,
        persona_data: Dict[str, Any],
        atleta_data: Optional[Dict[str, Any]],
        inscripcion_data: Optional[Dict[str, Any]],
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea una inscripción de atleta cumpliendo con UC-004 y UC-005.

        Args:
            persona_data: Datos personales (nombre, cédula, teléfono, dirección)
            atleta_data: Datos deportivos (fecha_nacimiento, sexo, tipo_sangre, etc.)
            inscripcion_data: Datos de inscripción (fecha, tipo)
            token: Token JWT para autenticación con microservicio externo

        Returns:
            Dict con estructura: {atleta: {...}, inscripcion: {...}, persona: {...}}

        Raises:
            ValidationError: Si hay datos duplicados o campos requeridos faltantes

        Reglas de Negocio:
        - Valida duplicados por cédula (UC-004 Curso Alterno 8)
        - Persiste datos localmente (no depende del microservicio externo)
        - Modo Fail-Safe: genera credenciales dummy si faltan
        """
        try:
            # 1. Validación básica de entrada
            if not persona_data:
                raise ValidationError(ErrorMessages.PERSONA_DATA_REQUIRED)

            atleta_data = atleta_data or {}
            inscripcion_data = inscripcion_data or {}

            # 2. Normalización de datos (DRY)
            normalized = self._normalize_atleta_data(persona_data)

            logger.info(
                f"[CREATE] Datos mapeados: cedula={normalized.cedula}, "
                f"nombre={normalized.nombre}, apellido={normalized.apellido}"
            )

            # 3. Validación de reglas de negocio
            self._validate_creation_rules(normalized)

            # 4. Validación de duplicados (UC-004 Curso Alterno 8)
            self._check_duplicate_inscripcion(normalized.cedula)

            # 5. Generación de credenciales fail-safe
            email, persona_data = self._generate_failsafe_credentials(
                normalized.cedula, persona_data
            )

            # 6. Sincronización con servicio externo
            persona_external = self._sync_external_service(
                persona_data, normalized.cedula, token
            )

            # 7. Persistencia local del atleta
            atleta = self._persist_local_atleta(
                normalized, email, persona_external, atleta_data
            )

            # 8. Persistencia local de la inscripción
            inscripcion = self._persist_local_inscripcion(atleta, inscripcion_data)

            # 9. Construcción de respuesta exitosa
            persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
            logger.info(
                f"[SUCCESS] Inscripción creada exitosamente. "
                f"Atleta ID={atleta.id}, Inscripción ID={inscripcion.id}"
            )
            return self._build_response(atleta, inscripcion, persona_info)

        except ValidationError:
            raise
        except Exception as e:
            logger.exception(
                f"[ERROR] Error inesperado en create_atleta_inscripcion: {e}"
            )
            raise ValidationError(f"{ErrorMessages.ERROR_INTERNO_GUARDAR}: {str(e)}")

    def update_atleta_inscripcion(
        self,
        inscripcion_id: int,
        persona_data: Optional[Dict[str, Any]],
        atleta_data: Optional[Dict[str, Any]],
        inscripcion_data: Optional[Dict[str, Any]],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza los datos de persona, atleta e inscripción.

        Args:
            inscripcion_id: ID de la inscripción a actualizar
            persona_data: Datos de persona a actualizar
            atleta_data: Datos de atleta a actualizar
            inscripcion_data: Datos de inscripción a actualizar
            token: Token de autenticación

        Returns:
            Dict con datos actualizados o None si no existe

        Raises:
            ValidationError: Si ocurre un error durante la actualización
        """
        try:
            inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
            if not inscripcion:
                return None

            atleta = inscripcion.atleta

            # Actualizar persona externa (si aplica)
            if persona_data:
                persona_payload = persona_data.copy()
                persona_payload.setdefault("external", atleta.persona_external)

                # Relleno de seguridad para update
                if "email" not in persona_payload:
                    persona_payload[
                        "email"
                    ] = f"update_{atleta.persona_external}@sistema.local"

                try:
                    self._call_user_module(
                        "post",
                        "/api/person/update",
                        token,
                        persona_payload,
                    )
                except Exception:
                    logger.warning(
                        "[UPDATE] Fallo API externa, solo se actualizará localmente"
                    )

                # CRÍTICO: Actualizar TODOS los datos personales LOCALMENTE
                # con MAPEO ROBUSTO
                nombre_real = (
                    persona_data.get("first_name")
                    or persona_data.get("firts_name")
                    or persona_data.get("nombres")
                    or persona_data.get("nombre")
                )
                apellido_real = (
                    persona_data.get("last_name")
                    or persona_data.get("apellidos")
                    or persona_data.get("apellido")
                )
                cedula_real = (
                    persona_data.get("identification")
                    or persona_data.get("cedula")
                    or persona_data.get("dni")
                )
                telefono_real = (
                    persona_data.get("phono")
                    or persona_data.get("telefono")
                    or persona_data.get("phone")
                )
                direccion_real = (
                    persona_data.get("direction")
                    or persona_data.get("direccion")
                    or persona_data.get("address")
                )
                email_real = persona_data.get("email") or persona_data.get("correo")
                genero_real = persona_data.get("gender") or persona_data.get("genero")

                local_update = {}
                if nombre_real:
                    local_update["nombres"] = nombre_real
                if apellido_real:
                    local_update["apellidos"] = apellido_real
                if cedula_real:
                    local_update["cedula"] = cedula_real
                if email_real:
                    local_update["email"] = email_real
                if telefono_real:
                    local_update["telefono"] = telefono_real
                if direccion_real:
                    local_update["direccion"] = direccion_real
                if genero_real:
                    local_update["genero"] = genero_real

                logger.info(f"[UPDATE MAPEO] local_update={local_update}")

                if local_update:
                    self.atleta_dao.update(atleta.id, **local_update)
                    atleta = self.atleta_dao.get_by_id(atleta.id)  # Refrescar

            # Actualizar Atleta Local (otros campos)
            if atleta_data:
                atleta = self._update_atleta_data(atleta, atleta_data)

            # Actualizar inscripción
            if inscripcion_data:
                inscripcion = self.inscripcion_dao.update(
                    inscripcion.id, **inscripcion_data
                )

            persona_info = self._fetch_persona(
                atleta.persona_external, token, allow_fail=True
            )
            return self._build_response(atleta, inscripcion, persona_info)

        except Exception as e:
            logger.error(f"Error actualizando: {e}")
            raise ValidationError(f"{ErrorMessages.ERROR_ACTUALIZAR}: {str(e)}")

    def _update_persona_data(
        self, atleta: Atleta, persona_data: Dict[str, Any], token: str
    ) -> Atleta:
        """
        Actualiza datos de persona en el microservicio y localmente.

        Args:
            atleta: Instancia del atleta
            persona_data: Datos a actualizar
            token: Token de autenticación

        Returns:
            Atleta actualizado
        """
        persona_payload = persona_data.copy()
        persona_payload.setdefault("external", atleta.persona_external)

        if "email" not in persona_payload:
            persona_payload["email"] = f"update_{atleta.persona_external}@sistema.local"

        try:
            self._call_user_module(
                "post",
                "/api/person/update",
                token,
                persona_payload,
            )
        except Exception:
            logger.warning("[UPDATE] Fallo API externa, solo se actualizará localmente")

        # Normalización usando el método DRY
        normalized = self._normalize_atleta_data(persona_data)
        local_update = self._extract_local_update_fields(normalized)

        logger.info(f"[UPDATE MAPEO] local_update={local_update}")

        if local_update:
            self.atleta_dao.update(atleta.id, **local_update)
            atleta = self.atleta_dao.get_by_id(atleta.id)

        return atleta

    def _update_atleta_data(
        self, atleta: Atleta, atleta_data: Dict[str, Any]
    ) -> Atleta:
        """
        Actualiza campos adicionales del atleta.

        Args:
            atleta: Instancia del atleta
            atleta_data: Datos a actualizar

        Returns:
            Atleta actualizado
        """
        valid_fields = [f.name for f in Atleta._meta.get_fields()]
        clean_data = {k: v for k, v in atleta_data.items() if k in valid_fields}
        return self.atleta_dao.update(atleta.id, **clean_data)

    def get_inscripcion_completa(
        self, inscripcion_id: int, token: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una inscripción completa por ID."""
        inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
        if not inscripcion:
            return None

        atleta = inscripcion.atleta
        persona_info = self._fetch_persona(
            atleta.persona_external, token, allow_fail=True
        )
        return self._build_response(atleta, inscripcion, persona_info)

    def list_inscripciones_completas(self, token: str) -> List[Dict[str, Any]]:
        """Lista todas las inscripciones completas."""
        inscripciones = self.inscripcion_dao.get_all()
        results = []
        for ins in inscripciones:
            atleta = ins.atleta
            persona_info = self._fetch_persona(
                atleta.persona_external, token, allow_fail=True
            )
            results.append(self._build_response(atleta, ins, persona_info))
        return results

    def list_inscripciones_completas_paginado(
        self, token: str, page: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Lista inscripciones con paginación.

        Args:
            token: Token de autenticación
            page: Número de página (comienza en 1)
            page_size: Cantidad de elementos por página

        Returns:
            Dict con datos paginados y metadatos de paginación
        """
        all_inscripciones = self.inscripcion_dao.get_all()
        total_items = all_inscripciones.count()

        total_pages = (
            (total_items + page_size - 1) // page_size if total_items > 0 else 1
        )
        page = max(1, min(page, total_pages))

        offset = (page - 1) * page_size
        inscripciones = all_inscripciones[offset : offset + page_size]

        results = []
        for ins in inscripciones:
            atleta = ins.atleta
            persona_info = self._fetch_persona(
                atleta.persona_external, token, allow_fail=True
            )
            results.append(self._build_response(atleta, ins, persona_info))

        return {
            "data": results,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        }

    def cambiar_estado_inscripcion(self, inscripcion_id: int) -> Optional[Inscripcion]:
        """Alterna el estado de habilitación de una inscripción."""
        inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
        if not inscripcion:
            return None
        nuevo_estado = not inscripcion.habilitada
        return self.inscripcion_dao.update(inscripcion_id, habilitada=nuevo_estado)
