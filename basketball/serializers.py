"""Serializadores del módulo Basketball."""

import requests
from django.conf import settings

# Importar todos los serializadores desde el archivo de barril
from .serializar import (  # noqa: F401
    PersonaSerializer,
    AdministradorSerializer,
    AdministradorDataSerializer,
    AdministradorInputSerializer,
    AdministradorResponseSerializer,
    EstudianteVinculacionSerializer,
    EstudianteVinculacionDataSerializer,
    EstudianteVinculacionInputSerializer,
    EstudianteVinculacionResponseSerializer,
    LoginSerializer,
    EntrenadorDataSerializer,
    EntrenadorSerializer,
    EntrenadorInputSerializer,
    EntrenadorResponseSerializer,
)

# Cache global para tokens y datos de persona
_user_module_token = None
_persona_cache = {}


def get_user_module_token():
    """Obtiene token del user_module con cache"""
    global _user_module_token
    if _user_module_token:
        return _user_module_token

    try:
        user_module_url = settings.USER_MODULE_URL
        admin_email = settings.USER_MODULE_ADMIN_EMAIL
        admin_password = settings.USER_MODULE_ADMIN_PASSWORD

        response = requests.post(
            f"{user_module_url}/api/person/login",
            json={"email": admin_email, "password": admin_password},
            timeout=5,
        )
        if response.status_code == 200:
            token = response.json().get("data", {}).get("token", "")
            # El token ya viene con el prefijo "Bearer "
            _user_module_token = (
                token.replace("Bearer ", "") if token.startswith("Bearer ") else token
            )
            return _user_module_token
    except Exception as e:
        print(f"Error obteniendo token: {e}")
    return None


def get_persona_from_user_module(persona_external):
    """Obtiene datos de persona del user_module con cache"""
    # Verificar cache
    if persona_external in _persona_cache:
        return _persona_cache[persona_external]

    token = get_user_module_token()
    if not token:
        return None

    try:
        user_module_url = settings.USER_MODULE_URL
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{user_module_url}/api/person/search/{persona_external}",
            headers=headers,
            timeout=5,
        )

        if response.status_code == 200:
            persona_data = response.json().get("data", {})
            _persona_cache[persona_external] = persona_data
            return persona_data
        elif response.status_code == 401:
            # Token expiró, limpiar cache y reintentar
            global _user_module_token
            _user_module_token = None
            token = get_user_module_token()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(
                    f"{user_module_url}/api/person/search/{persona_external}",
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    persona_data = response.json().get("data", {})
                    _persona_cache[persona_external] = persona_data
                    return persona_data
    except Exception as e:
        print(f"Error obteniendo datos de persona {persona_external}: {e}")

    return None
