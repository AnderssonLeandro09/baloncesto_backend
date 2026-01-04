"""
Servicio de negocio para Inscripciones.
CORREGIDO: Eliminada obligatoriedad de email/password según diagrama de clases.
MODO FAIL-SAFE: El sistema continúa funcionando aunque el microservicio de usuarios falle.
"""

import logging
import time
import traceback
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
        # Aseguramos que la URL no termine en slash
        self.user_module_url = (settings.USER_MODULE_URL or "").rstrip("/")

    # ======================================================================
    # Helper HTTP
    # ======================================================================
    def _build_auth_header(self, token: Optional[str]) -> Dict[str, str]:
        if not token:
            # Fallback silencioso para desarrollo
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
        # Validación de configuración
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
            # MODO OFFLINE: El microservicio no está disponible
            logger.warning(f"[MODO OFFLINE] Microservicio de usuarios no disponible: {url}")
            logger.debug(f"Detalle conexión: {exc}")
            return {"offline": True, "data": {"external_id": f"offline_{int(time.time())}"}}
        except requests.exceptions.Timeout as exc:
            logger.warning(f"[TIMEOUT] El microservicio tardó demasiado: {url}")
            return {"timeout": True, "data": {"external_id": f"timeout_{int(time.time())}"}}
        except requests.RequestException as exc:
            logger.error(f"[ERROR CONEXIÓN] Fallo inesperado user_module {url}: {exc}")
            # Retornamos vacío para permitir fallback
            return {}

        if response.status_code >= 400:
            message = self._extract_message(response)
            # Ignoramos error de "ya existe" para no bloquear inscripciones repetidas
            if "ya existe" not in str(message).lower() and "already" not in str(message).lower():
                logger.warning(f"Error externo no fatal ({response.status_code}): {message}")

        try:
            return response.json()
        except ValueError:
            return {}

    def _extract_message(self, response) -> str:
        try:
            data = response.json()
            return data.get("message") or str(data)
        except Exception:
            return response.text or "error desconocido"

    def _extract_external(self, response_data: Dict[str, Any]) -> Optional[str]:
        if not response_data:
            return None
        data = response_data.get("data")
        # Soporte para respuestas anidadas o planas
        if isinstance(data, dict):
            return data.get("external_id") or data.get("external") or data.get("id")
        if isinstance(response_data, dict):
            return response_data.get("external_id")
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
        
        # RESPUESTA HÍBRIDA: Prioriza datos locales, complementa con externos
        persona_response = {
            "first_name": atleta.nombres or persona_externa.get("first_name", ""),
            "last_name": atleta.apellidos or persona_externa.get("last_name", ""),
            "identification": atleta.cedula or persona_externa.get("identification", ""),
            "email": atleta.email or persona_externa.get("email", ""),
            "phono": atleta.telefono or persona_externa.get("phono", ""),
            "direction": atleta.direccion or persona_externa.get("direction", ""),
            "gender": atleta.genero or atleta.sexo or persona_externa.get("gender", ""),
        }
        
        return {
            "atleta": {
                "id": atleta.id,
                "persona_external": atleta.persona_external,
                # Datos locales redundantes
                "nombres": atleta.nombres,
                "apellidos": atleta.apellidos,
                "cedula": atleta.cedula,
                "email": atleta.email,
                "direccion": atleta.direccion,
                "genero": atleta.genero,
                # Otros datos
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
        atleta_data: Dict[str, Any],
        inscripcion_data: Dict[str, Any],
        token: str = None,
    ) -> Dict[str, Any]:
        """
        Crea una inscripción de atleta cumpliendo con UC-004 y UC-005.
        
        Reglas de Negocio:
        - Valida duplicados por cédula (Curso Alterno 8)
        - Persiste datos localmente (no depende del microservicio externo)
        - Modo Fail-Safe: genera credenciales dummy si faltan
        """
        try:
            # ============================================================
            # 1. VALIDACIÓN BÁSICA DE ENTRADA
            # ============================================================
            if not persona_data:
                raise ValidationError("Datos de persona son requeridos")

            atleta_data = atleta_data or {}
            inscripcion_data = inscripcion_data or {}
            
            # ============================================================
            # 2. MAPEO ROBUSTO DE DATOS (Frontend -> BD Local)
            # Soporta múltiples nombres de campo para evitar errores por typos
            # ============================================================
            cedula = (
                persona_data.get('identification') or 
                persona_data.get('cedula') or 
                persona_data.get('dni') or 
                ""
            )
            nombre = (
                persona_data.get('first_name') or 
                persona_data.get('firts_name') or  # Typo común del frontend
                persona_data.get('nombres') or 
                persona_data.get('nombre') or 
                ""
            )
            apellido = (
                persona_data.get('last_name') or 
                persona_data.get('apellidos') or 
                persona_data.get('apellido') or 
                ""
            )
            telefono = (
                persona_data.get('phono') or 
                persona_data.get('telefono') or 
                persona_data.get('phone') or 
                persona_data.get('celular') or 
                ""
            )
            direccion = (
                persona_data.get('direction') or 
                persona_data.get('direccion') or 
                persona_data.get('address') or 
                ""
            )
            email = (
                persona_data.get('email') or 
                persona_data.get('correo') or 
                ""
            )
            genero = (
                persona_data.get('gender') or 
                persona_data.get('genero') or 
                persona_data.get('sexo') or 
                ""
            )
            
            logger.info(f"[CREATE] Datos mapeados: cedula={cedula}, nombre={nombre}, apellido={apellido}")
            
            # ============================================================
            # 3. VALIDACIÓN DE DUPLICADOS (UC-004 Curso Alterno 8)
            # Verificar si ya existe una inscripción ACTIVA con esta cédula
            # ============================================================
            if cedula:
                # Buscar atleta existente por cédula
                atleta_existente = self.atleta_dao.get_by_filter(cedula=cedula).first()
                
                if atleta_existente:
                    # Verificar si tiene inscripción activa
                    inscripcion_activa = self.inscripcion_dao.get_by_filter(
                        atleta=atleta_existente, 
                        habilitada=True
                    ).first()
                    
                    if inscripcion_activa:
                        logger.warning(f"[DUPLICADO] Atleta con cédula {cedula} ya tiene inscripción activa ID={inscripcion_activa.id}")
                        raise ValidationError("El atleta ya se encuentra registrado con una inscripción activa.")
            
            # ============================================================
            # 4. GENERACIÓN DE CREDENCIALES DUMMY (Modo Fail-Safe)
            # Si no viene email/password, generamos unos técnicos
            # ============================================================
            if not email:
                email = f"atleta_{cedula}_{int(time.time())}@local.system"
                logger.info(f"[FAIL-SAFE] Email dummy generado: {email}")
            
            if not persona_data.get("password"):
                persona_data["password"] = "System_Auto_Pass_123$"
            
            # Actualizar persona_data con email generado
            persona_data["email"] = email
            
            # ============================================================
            # 5. OBTENCIÓN DE ID EXTERNO (Opcional - Fail-Safe)
            # Intentamos registrar en el microservicio, pero continuamos si falla
            # ============================================================
            persona_external = None
            
            try:
                persona_response = self._call_user_module(
                    "post", "/api/person/save-account", token, persona_data
                )
                persona_external = self._extract_external(persona_response)

                if not persona_external and cedula:
                    lookup_response = self._search_by_identification(cedula, token)
                    persona_external = self._extract_external(lookup_response)
            except Exception as ext_err:
                logger.warning(f"[MODO OFFLINE] Error con microservicio externo: {ext_err}")
                # Intentar búsqueda silenciosa
                try:
                    if cedula:
                        lookup_response = self._search_by_identification(cedula, token)
                        persona_external = self._extract_external(lookup_response)
                except Exception:
                    pass
            
            # Fallback: ID local si no hay conexión externa
            if not persona_external:
                persona_external = f"local_{cedula or 'unknown'}_{int(time.time())}"
                logger.info(f"[MODO OFFLINE] ID local generado: {persona_external}")
            
            # ============================================================
            # 6. CREACIÓN/ACTUALIZACIÓN DE ATLETA EN BD LOCAL
            # Esta es la fuente de verdad - no depende del microservicio
            # ============================================================
            datos_atleta_local = {
                'nombres': nombre,
                'apellidos': apellido,
                'cedula': cedula,
                'email': email,
                'telefono': telefono,
                'direccion': direccion,
                'genero': genero,
            }
            
            # Agregar campos adicionales de atleta_data (edad, sexo, etc.)
            valid_fields = [f.name for f in Atleta._meta.get_fields()]
            for key, value in (atleta_data or {}).items():
                if key in valid_fields and value is not None:
                    datos_atleta_local[key] = value
            
            # Verificar si ya existe atleta con este persona_external
            atleta_por_external = self.atleta_dao.get_by_filter(persona_external=persona_external).first()
            # También verificar por cédula (puede existir con otro external)
            atleta_por_cedula = self.atleta_dao.get_by_filter(cedula=cedula).first() if cedula else None
            
            atleta = atleta_por_external or atleta_por_cedula
            
            if atleta:
                # Actualizar atleta existente
                logger.info(f"[UPDATE] Actualizando atleta ID={atleta.id}")
                clean_data = {k: v for k, v in datos_atleta_local.items() if k in valid_fields and v}
                if not atleta.persona_external or atleta.persona_external.startswith('local_'):
                    clean_data['persona_external'] = persona_external
                self.atleta_dao.update(atleta.id, **clean_data)
                atleta = self.atleta_dao.get_by_id(atleta.id)
            else:
                # Crear nuevo atleta
                logger.info(f"[CREATE] Creando nuevo atleta con cédula={cedula}")
                clean_data = {k: v for k, v in datos_atleta_local.items() if k in valid_fields and v}
                atleta = self.atleta_dao.create(persona_external=persona_external, **clean_data)
            
            # ============================================================
            # 7. GESTIÓN DE INSCRIPCIÓN
            # ============================================================
            inscripcion = self.inscripcion_dao.get_by_filter(atleta=atleta).first()
            
            if inscripcion:
                # Si existe inscripción (deshabilitada), reactivarla
                logger.info(f"[REACTIVAR] Inscripción existente ID={inscripcion.id}")
                update_data = {'habilitada': True}
                if inscripcion_data:
                    update_data.update(inscripcion_data)
                self.inscripcion_dao.update(inscripcion.id, **update_data)
                inscripcion = self.inscripcion_dao.get_by_id(inscripcion.id)
            else:
                # Crear nueva inscripción
                logger.info(f"[CREATE] Creando nueva inscripción para atleta ID={atleta.id}")
                inscripcion_params = {
                    "atleta": atleta,
                    "fecha_inscripcion": date.today(),
                    "tipo_inscripcion": inscripcion_data.get("tipo_inscripcion", "MAYOR_EDAD"),
                    "habilitada": True,
                }
                # Solo agregar campos válidos de inscripcion_data
                valid_insc_fields = [f.name for f in Inscripcion._meta.get_fields()]
                for key, value in inscripcion_data.items():
                    if key in valid_insc_fields and key not in inscripcion_params:
                        inscripcion_params[key] = value
                inscripcion = self.inscripcion_dao.create(**inscripcion_params)

            # ============================================================
            # 8. CONSTRUIR RESPUESTA EXITOSA
            # ============================================================
            persona_info = self._fetch_persona(persona_external, token, allow_fail=True)
            logger.info(f"[SUCCESS] Inscripción creada exitosamente. Atleta ID={atleta.id}, Inscripción ID={inscripcion.id}")
            return self._build_response(atleta, inscripcion, persona_info)
            
        except ValidationError:
            # Re-lanzar errores de validación (duplicados, datos faltantes)
            raise
        except Exception as e:
            logger.exception(f"[ERROR] Error inesperado en create_atleta_inscripcion: {e}")
            raise ValidationError(f"Error interno al guardar: {str(e)}")

    def update_atleta_inscripcion(
        self,
        inscripcion_id: int,
        persona_data: Dict[str, Any],
        atleta_data: Dict[str, Any],
        inscripcion_data: Dict[str, Any],
        token: str,
    ) -> Optional[Dict[str, Any]]:
        
        try:
            inscripcion = self.inscripcion_dao.get_by_id(inscripcion_id)
            if not inscripcion:
                return None

            atleta = inscripcion.atleta

            # Actualizar Persona Externa (si aplica)
            if persona_data:
                persona_payload = persona_data.copy()
                persona_payload.setdefault("external", atleta.persona_external)
                
                # Relleno de seguridad para update
                if "email" not in persona_payload:
                     persona_payload["email"] = f"update_{atleta.persona_external}@sistema.local"
                
                try:
                    self._call_user_module("post", "/api/person/update", token, persona_payload)
                except Exception:
                    logger.warning("[UPDATE] Fallo API externa, solo se actualizará localmente")

                # CRÍTICO: Actualizar TODOS los datos personales LOCALMENTE con MAPEO ROBUSTO
                nombre_real = (
                    persona_data.get('first_name') or 
                    persona_data.get('firts_name') or 
                    persona_data.get('nombres') or 
                    persona_data.get('nombre')
                )
                apellido_real = (
                    persona_data.get('last_name') or 
                    persona_data.get('apellidos') or 
                    persona_data.get('apellido')
                )
                cedula_real = (
                    persona_data.get('identification') or 
                    persona_data.get('cedula') or 
                    persona_data.get('dni')
                )
                telefono_real = (
                    persona_data.get('phono') or 
                    persona_data.get('telefono') or 
                    persona_data.get('phone')
                )
                direccion_real = (
                    persona_data.get('direction') or 
                    persona_data.get('direccion') or 
                    persona_data.get('address')
                )
                email_real = (
                    persona_data.get('email') or 
                    persona_data.get('correo')
                )
                genero_real = (
                    persona_data.get('gender') or 
                    persona_data.get('genero')
                )
                
                local_update = {}
                if nombre_real:
                    local_update['nombres'] = nombre_real
                if apellido_real:
                    local_update['apellidos'] = apellido_real
                if cedula_real:
                    local_update['cedula'] = cedula_real
                if email_real:
                    local_update['email'] = email_real
                if telefono_real:
                    local_update['telefono'] = telefono_real
                if direccion_real:
                    local_update['direccion'] = direccion_real
                if genero_real:
                    local_update['genero'] = genero_real
                
                logger.info(f"[UPDATE MAPEO] local_update={local_update}")
                
                if local_update:
                    self.atleta_dao.update(atleta.id, **local_update)
                    atleta = self.atleta_dao.get_by_id(atleta.id)  # Refrescar

            # Actualizar Atleta Local (otros campos)
            if atleta_data:
                valid_fields = [f.name for f in Atleta._meta.get_fields()]
                clean_data = {k: v for k, v in atleta_data.items() if k in valid_fields}
                atleta = self.atleta_dao.update(atleta.id, **clean_data)

            # Actualizar Inscripción
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
            raise ValidationError(f"Error al actualizar: {str(e)}")

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