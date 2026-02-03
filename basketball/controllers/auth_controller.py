"""Controlador de Autenticación."""

import jwt
import requests
import datetime
import logging
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from ..models import Administrador, Entrenador, EstudianteVinculacion
from ..serializers import LoginSerializer

logger = logging.getLogger(__name__)


class AuthController(viewsets.ViewSet):
    """
    Maneja la autenticación actuando como proxy hacia el microservicio de usuarios
    y generando un JWT local con los roles del sistema de baloncesto.
    """

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
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # 1. Validar credenciales contra Microservicio de Usuarios
        user_module_url = getattr(settings, "USER_MODULE_URL", "http://localhost:8096")
        login_url = f"{user_module_url}/api/person/login"

        try:
            # Enviamos las credenciales tal cual al otro servicio
            response = requests.post(
                login_url,
                json={"email": email, "password": password},
                timeout=8,
            )
        except requests.RequestException as e:
            logger.error(f"Error conectando al servicio de usuarios: {e}")
            return Response(
                {"error": "No se pudo conectar con el servidor"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if response.status_code != 200:
            # Manejar errores específicos del microservicio de usuarios
            error_msg = self._extract_error_message(response)

            # Mapear errores comunes a mensajes amigables
            if response.status_code == 401:
                return Response(
                    {"error": "Clave incorrecta"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            elif response.status_code == 404:
                return Response(
                    {"error": "La cuenta no existe"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            else:
                response_status = (
                    response.status_code
                    if response.status_code < 500
                    else status.HTTP_502_BAD_GATEWAY
                )
                return Response(
                    {"error": error_msg or "Error en el servicio de autenticación"},
                    status=response_status,
                )

        # 2. Extraer información del usuario
        try:
            resp_json = response.json()
            user_data = resp_json.get("data", {})

            # El ID externo suele venir en 'external' o 'id'
            external_id = user_data.get("external")
            if not external_id:
                # Fallback por si la estructura cambia
                external_id = user_data.get("id")

            if not external_id:
                logger.error(f"Respuesta de login sin ID externo: {resp_json}")
                return Response(
                    {"error": "Error obteniendo identidad del usuario"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        except ValueError:
            return Response(
                {"error": "Respuesta inválida del servicio de usuarios"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3. Determinar Rol Local en nuestra BD
        role = "USER"  # Rol por defecto

        logger.info(f"Login attempt for external_id: '{external_id}'")

        # Verificamos jerárquicamente
        is_admin = Administrador.objects.filter(
            persona_external=external_id, estado=True
        ).exists()
        logger.info(f"Is Admin? {is_admin}")

        if is_admin:
            role = "ADMIN"
        else:
            # Verificar si es Entrenador
            entrenador = Entrenador.objects.filter(persona_external=external_id).first()
            if entrenador:
                if entrenador.eliminado:
                    return Response(
                        {"error": "La cuenta está inactiva."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                role = "ENTRENADOR"
            else:
                # Verificar si es Estudiante de Vinculación
                estudiante = EstudianteVinculacion.objects.filter(
                    persona_external=external_id
                ).first()
                if estudiante:
                    if estudiante.eliminado:
                        return Response(
                            {"error": "La cuenta está inactiva."},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                    role = "ESTUDIANTE_VINCULACION"

        # 4. Generar Nuestro JWT Local
        # Usamos la SECRET_KEY de Django para firmar
        token_payload = {
            "sub": external_id,  # Subject: ID del usuario
            "role": role,  # Nuestro rol calculado
            "email": email,
            "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=1),  # Expira en 1 día
            "iat": datetime.datetime.utcnow(),
        }

        local_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

        # Retornamos el token y datos útiles para el frontend
        return Response(
            {
                "token": local_token,
                "user": {
                    "id": external_id,
                    "email": email,
                    "role": role,
                    "name": token_payload["name"],
                },
            }
        )

    def _extract_error_message(self, response):
        """Extrae el mensaje de error de la respuesta del microservicio."""
        try:
            resp_json = response.json()
            # Intentar diferentes formatos de respuesta de error
            if isinstance(resp_json, dict):
                return (
                    resp_json.get("error")
                    or resp_json.get("message")
                    or resp_json.get("detail")
                    or resp_json.get("msg")
                )
            return str(resp_json)
        except ValueError:
            return None
