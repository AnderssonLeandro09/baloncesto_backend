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
        token: str,
    ) -> Dict[str, Any]:
        
        # 1. Validación mínima (Solo datos personales básicos)
        if not persona_data:
            raise ValidationError("Datos de persona son requeridos")

        atleta_data = atleta_data or {}
        inscripcion_data = inscripcion_data or {}
        
        # 2. GENERACIÓN INTERNA DE CREDENCIALES (Invisible)
        # Como el atleta NO tiene usuario, generamos datos técnicos dummy
        # para satisfacer al sistema externo sin molestar al usuario.
        if not persona_data.get("email"):
            unique_id = str(int(time.time()))
            ident = persona_data.get('identification', unique_id)
            # Email técnico interno
            persona_data["email"] = f"atleta_{ident}@sistema.local"
            
        if not persona_data.get("password"):
            # Password técnico interno
            persona_data["password"] = "System_Auto_Pass_123$"

        persona_external = None

        # 3. Obtención de ID Externo (Fail-Safe)
        try:
            # Intentar registrar en sistema externo
            persona_response = self._call_user_module(
                "post", "/api/person/save-account", token, persona_data
            )
            persona_external = self._extract_external(persona_response)

            # Si falla (ej: ya existe), buscamos por cédula
            if not persona_external and persona_data.get("identification"):
                lookup_response = self._search_by_identification(
                    persona_data.get("identification"), token
                )
                persona_external = self._extract_external(lookup_response)

        except Exception:
            # Si el sistema externo falla totalmente, intentamos búsqueda silenciosa
            try:
                if persona_data.get("identification"):
                    lookup_response = self._search_by_identification(
                        persona_data.get("identification"), token
                    )
                    persona_external = self._extract_external(lookup_response)
            except Exception as search_err:
                logger.warning(f"[FALLBACK] Búsqueda por cédula también falló: {search_err}")
        
        # FALLBACK: Generar ID local si no hay conexión externa
        # SIEMPRE permitimos continuar para evitar Error 500
        if not persona_external:
            logger.warning("[MODO OFFLINE] Generando ID Local temporal (Fallo API Externa)")
            persona_external = f"local_{persona_data.get('identification', 'unknown')}_{int(time.time())}"

        # 4. Creación Local (Base de datos local)
        try:
            # MAPEO ROBUSTO: Buscar en múltiples claves posibles (maneja typos del frontend)
            nombre_real = (
                persona_data.get('first_name') or 
                persona_data.get('firts_name') or  # Typo común
                persona_data.get('nombres') or 
                persona_data.get('nombre') or 
                ""
            )
            apellido_real = (
                persona_data.get('last_name') or 
                persona_data.get('apellidos') or 
                persona_data.get('apellido') or 
                ""
            )
            cedula_real = (
                persona_data.get('identification') or 
                persona_data.get('cedula') or 
                persona_data.get('dni') or 
                ""
            )
            telefono_real = (
                persona_data.get('phono') or 
                persona_data.get('telefono') or 
                persona_data.get('phone') or 
                persona_data.get('celular') or 
                ""
            )
            direccion_real = (
                persona_data.get('direction') or 
                persona_data.get('direccion') or 
                persona_data.get('address') or 
                ""
            )
            email_real = (
                persona_data.get('email') or 
                persona_data.get('correo') or 
                ""
            )
            genero_real = (
                persona_data.get('gender') or 
                persona_data.get('genero') or 
                persona_data.get('sexo') or 
                ""
            )
            
            # Log para debugging
            logger.info(f"[MAPEO] nombre={nombre_real}, apellido={apellido_real}, cedula={cedula_real}")
            
            datos_persona_local = {
                'nombres': nombre_real,
                'apellidos': apellido_real,
                'cedula': cedula_real,
                'email': email_real,
                'telefono': telefono_real,
                'direccion': direccion_real,
                'genero': genero_real,
            }
            
            # Verificar existencia previa
            if self.atleta_dao.exists(persona_external=persona_external):
                atleta = self.atleta_dao.get_by_filter(
                    persona_external=persona_external
                ).first()
                # Actualizar datos si existen cambios
                if atleta:
                    valid_fields = [f.name for f in Atleta._meta.get_fields()]
                    # Combinar datos de atleta_data con datos de persona
                    clean_data = {k: v for k, v in (atleta_data or {}).items() if k in valid_fields}
                    # Agregar TODOS los datos personales
                    for key, value in datos_persona_local.items():
                        if value:  # Solo si tiene valor
                            clean_data[key] = value
                    self.atleta_dao.update(atleta.id, **clean_data)
                    atleta = self.atleta_dao.get_by_id(atleta.id)  # Refrescar
            else:
                # Crear nuevo atleta
                valid_fields = [f.name for f in Atleta._meta.get_fields()]
                # Combinar datos de atleta_data con datos de persona
                clean_data = {k: v for k, v in (atleta_data or {}).items() if k in valid_fields}
                # Agregar TODOS los datos personales
                for key, value in datos_persona_local.items():
                    if value:  # Solo si tiene valor
                        clean_data[key] = value
                
                atleta = self.atleta_dao.create(
                    persona_external=persona_external, **clean_data
                )

            # 5. Gestión de Inscripción
            inscripcion = self.inscripcion_dao.get_by_filter(atleta=atleta).first()
            
            if inscripcion:
                # Si existe, habilitar y actualizar
                if not inscripcion.habilitada:
                    self.inscripcion_dao.update(inscripcion.id, habilitada=True)
                
                if inscripcion_data:
                    self.inscripcion_dao.update(inscripcion.id, **inscripcion_data)
                
                inscripcion = self.inscripcion_dao.get_by_id(inscripcion.id)
            else:
                # Crear nueva inscripción
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
            
        except Exception as e:
            logger.exception("Error guardando datos locales")
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