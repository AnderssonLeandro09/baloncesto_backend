"""Controlador de Autenticación."""

import jwt
import requests
from datetime import datetime, timedelta, timezone
import logging
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from ..models import Administrador, Entrenador, EstudianteVinculacion
from ..serializers import LoginSerializer

logger = logging.getLogger(__name__)

# Constantes para mensajes de error
ERROR_CUENTA_INACTIVA = "La cuenta está inactiva."
ERROR_SERVICIO_NO_DISPONIBLE = (
    "Servicio de autenticación no disponible. Intente más tarde."
)
ERROR_IDENTIDAD_USUARIO = "Error obteniendo identidad del usuario"
ERROR_RESPUESTA_INVALIDA = "Respuesta inválida del servicio de usuarios"


class AuthController(viewsets.ViewSet):
    """
    Maneja la autenticación actuando como proxy hacia el microservicio de usuarios
    y generando un JWT local con los roles del sistema de baloncesto.
    """

    def _authenticate_with_user_service(self, email: str, password: str):
        """Valida credenciales contra el microservicio de usuarios."""
        user_module_url = getattr(settings, "USER_MODULE_URL", "http://localhost:8096")
        login_url = f"{user_module_url}/api/person/login"

        try:
            response = requests.post(
                login_url,
                json={"email": email, "password": password},
                timeout=8,
            )
            return response
        except requests.RequestException as e:
            logger.error("Error conectando al servicio de usuarios: %s", e)
            return None

    def _extract_error_message(self, response) -> str:
        """Extrae y mapea el mensaje de error de la respuesta."""
        error_msg = "Credenciales inválidas"
        try:
            resp_json = response.json()
            error_msg = (
                resp_json.get("msg")
                or resp_json.get("message")
                or resp_json.get("error")
                or error_msg
            )

            if response.status_code == 404:
                return "El correo electrónico no está registrado."

            if response.status_code == 401:
                return self._map_401_error(error_msg)

        except ValueError:
            pass
        return error_msg

    def _map_401_error(self, error_msg: str) -> str:
        """Mapea errores 401 a mensajes específicos."""
        error_lower = str(error_msg).lower()
        if "password" in error_lower or "contraseña" in error_lower:
            return "La contraseña es incorrecta."
        if "account" in error_lower or "cuenta" in error_lower:
            return "La cuenta tiene problemas (bloqueada/inactiva)."
        return "Credenciales incorrectas (correo o contraseña)."

    def _extract_user_data(self, response):
        """Extrae datos del usuario de la respuesta."""
        try:
            resp_json = response.json()
            user_data = resp_json.get("data", {})
            external_id = user_data.get("external") or user_data.get("id")
            return user_data, external_id
        except ValueError:
            return None, None

    def _determine_role(self, external_id: str):
        """Determina el rol del usuario en el sistema local."""
        logger.info("Login attempt for external_id: '%s'", external_id)

        # Verificar si es Administrador
        if Administrador.objects.filter(
            persona_external=external_id, estado=True
        ).exists():
            logger.info("Is Admin? True")
            return "ADMIN", None

        # Verificar si es Entrenador
        entrenador = Entrenador.objects.filter(persona_external=external_id).first()
        if entrenador:
            if entrenador.eliminado:
                return None, ERROR_CUENTA_INACTIVA
            return "ENTRENADOR", None

        # Verificar si es Estudiante de Vinculación
        estudiante = EstudianteVinculacion.objects.filter(
            persona_external=external_id
        ).first()
        if estudiante:
            if estudiante.eliminado:
                return None, ERROR_CUENTA_INACTIVA
            return "ESTUDIANTE_VINCULACION", None

        return "USER", None

    def _generate_jwt(self, external_id: str, role: str, email: str, user_data: dict):
        """Genera el token JWT local."""
        now = datetime.now(timezone.utc)
        name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()

        token_payload = {
            "sub": external_id,
            "role": role,
            "email": email,
            "name": name,
            "exp": now + timedelta(days=1),
            "iat": now,
        }

        return jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256"), name

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user": {"type": "object"},
                },
            }
        },
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        """Procesa el login del usuario."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # 1. Autenticar con el microservicio
        response = self._authenticate_with_user_service(email, password)
        if response is None:
            return Response(
                {"error": ERROR_SERVICIO_NO_DISPONIBLE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # 2. Manejar error de autenticación
        if response.status_code != 200:
            error_msg = self._extract_error_message(response)
            response_status = (
                response.status_code
                if response.status_code < 500
                else status.HTTP_502_BAD_GATEWAY
            error_msg = "Credenciales inválidas"
            try:
                resp_json = response.json()
                # Intentar obtener el mensaje de error del servicio externo
                # Puede venir en 'msg', 'message', 'error' o 'data'
                error_msg = (
                    resp_json.get("msg")
                    or resp_json.get("message")
                    or resp_json.get("error")
                    or error_msg
                )

                # Si el mensaje es muy genérico o técnico, podemos mapearlo
                if response.status_code == 404:
                    error_msg = "El correo electrónico no está registrado."
                elif response.status_code == 401:
                    if (
                        "password" in str(error_msg).lower()
                        or "contraseña" in str(error_msg).lower()
                    ):
                        error_msg = "La contraseña es incorrecta."
                    elif (
                        "account" in str(error_msg).lower()
                        or "cuenta" in str(error_msg).lower()
                    ):
                        error_msg = "La cuenta tiene problemas (bloqueada/inactiva)."
                    else:
                        error_msg = "Credenciales incorrectas (correo o contraseña)."
            except ValueError:
                pass

            return Response(
                {"error": error_msg},
                status=(
                    response.status_code
                    if response.status_code < 500
                    else status.HTTP_502_BAD_GATEWAY
                ),
            )
            return Response({"error": error_msg}, status=response_status)

        # 3. Extraer datos del usuario
        user_data, external_id = self._extract_user_data(response)
        if not external_id:
            logger.error("Respuesta de login sin ID externo: %s", response.text)
            return Response(
                {"error": ERROR_IDENTIDAD_USUARIO},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if user_data is None:
            return Response(
                {"error": ERROR_RESPUESTA_INVALIDA},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 4. Determinar rol local
        role, error = self._determine_role(external_id)
        if error:
            return Response(
                {"error": error},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 5. Generar JWT
        local_token, name = self._generate_jwt(external_id, role, email, user_data)

        return Response(
            {
                "token": local_token,
                "user": {
                    "id": external_id,
                    "email": email,
                    "role": role,
                    "name": name,
                },
            }
        )
