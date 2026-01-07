import logging
import traceback
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..models import Inscripcion
from ..services.inscripcion_service import InscripcionService
from ..serializers import (
    InscripcionSerializer,
    AtletaInscripcionInputSerializer,
    AtletaInscripcionResponseSerializer,
    get_user_module_token,
)

logger = logging.getLogger(__name__)


class InscripcionController(viewsets.ViewSet):
    """
    Controlador para gestionar las Inscripciones de los atletas.
    MODO DEBUG: Acceso público temporal para depuración del Error 500.
    """

    # CRÍTICO: Desactivar autenticación para evitar conexión al User-Service
    permission_classes = [AllowAny]
    authentication_classes = []  # Evita que Django intente validar tokens
    serializer_class = InscripcionSerializer
    service = InscripcionService()

    @extend_schema(responses={200: AtletaInscripcionResponseSerializer(many=True)})
    def list(self, request):
        """Lista todas las inscripciones con datos de persona y atleta."""
        token = get_user_module_token()
        try:
            data = self.service.list_inscripciones_completas(token)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en list inscripciones: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=AtletaInscripcionInputSerializer,
        responses={201: AtletaInscripcionResponseSerializer},
    )
    def create(self, request):
        """
        Crea un atleta y su inscripción directamente.
        FAIL-SAFE: Captura todos los errores y devuelve mensajes legibles.
        """
        try:
            token = get_user_module_token()
            payload = request.data
            persona_data = payload.get("persona")
            atleta_data = payload.get("atleta")
            inscripcion_data = payload.get("inscripcion")

            # Validación básica antes de procesar
            if not persona_data:
                return Response(
                    {"detail": "ERROR: Datos de persona son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = self.service.create_atleta_inscripcion(
                persona_data, atleta_data, inscripcion_data, token
            )
            return Response(result, status=status.HTTP_201_CREATED)

        except ValidationError as exc:
            # Error de validación controlado
            logger.warning(f"Validación fallida en create inscripcion: {exc}")
            return Response(
                {"detail": f"Error de validación: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            # Error inesperado - logueamos el traceback completo
            logger.error(f"ERROR INTERNO en create inscripcion: {exc}")
            traceback.print_exc()  # Imprime el error completo en consola
            return Response(
                {"detail": f"ERROR INTERNO BACKEND: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(responses={200: AtletaInscripcionResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene una inscripción completa por ID."""
        token = get_user_module_token()
        try:
            data = self.service.get_inscripcion_completa(pk, token)
            if not data:
                return Response(
                    {"error": "Inscripción no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en retrieve inscripcion: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=AtletaInscripcionInputSerializer,
        responses={200: AtletaInscripcionResponseSerializer},
    )
    def update(self, request, pk=None):
        """
        Actualiza los datos de la persona, atleta e inscripción.
        FAIL-SAFE: Captura todos los errores y devuelve mensajes legibles.
        """
        try:
            token = get_user_module_token()
            payload = request.data
            persona_data = payload.get("persona")
            atleta_data = payload.get("atleta")
            inscripcion_data = payload.get("inscripcion")

            result = self.service.update_atleta_inscripcion(
                pk, persona_data, atleta_data, inscripcion_data, token
            )
            if not result:
                return Response(
                    {"detail": "Inscripción no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)

        except ValidationError as exc:
            logger.warning(f"Validación fallida en update inscripcion: {exc}")
            return Response(
                {"detail": f"Error de validación: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error(f"ERROR INTERNO en update inscripcion: {exc}")
            traceback.print_exc()
            return Response(
                {"detail": f"ERROR INTERNO BACKEND: {str(exc)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    @extend_schema(request=None)
    def cambiar_estado(self, request, pk=None):
        """
        Alterna el estado de habilitación de una inscripción (Toggle).
        No requiere cuerpo en la petición.
        """
        try:
            inscripcion = self.service.cambiar_estado_inscripcion(pk)
            if not inscripcion:
                return Response(
                    {"error": "Inscripción no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            mensaje = (
                "Inscripción habilitada correctamente"
                if inscripcion.habilitada
                else "Inscripción deshabilitada correctamente"
            )
            return Response(
                {"habilitada": inscripcion.habilitada, "mensaje": mensaje},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.error(f"Error en cambiar_estado inscripcion: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="verificar-cedula")
    @extend_schema(
        parameters=[
            {
                "name": "dni",
                "in": "query",
                "required": True,
                "description": "Número de cédula/DNI del atleta a verificar",
                "schema": {"type": "string"},
            }
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "existe": {"type": "boolean"},
                    "mensaje": {"type": "string"},
                },
            }
        },
    )
    def verificar_cedula(self, request):
        """
        Verifica si existe una inscripción activa para un DNI/cédula.
        Útil para validación en tiempo real desde el frontend.

        GET /api/inscripciones/verificar-cedula/?dni=1234567890
        """
        dni = request.query_params.get("dni")

        if not dni:
            return Response(
                {"error": "DNI requerido", "existe": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Buscar inscripción activa por cédula del atleta
        existe = Inscripcion.objects.filter(
            atleta__cedula=dni, habilitada=True
        ).exists()

        return Response(
            {
                "existe": existe,
                "mensaje": (
                    "El atleta ya se encuentra registrado"
                    if existe
                    else "Disponible para inscripción"
                ),
            },
            status=status.HTTP_200_OK,
        )
