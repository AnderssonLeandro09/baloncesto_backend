import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.inscripcion_service import InscripcionService
from ..serializers import (
    InscripcionSerializer,
    AtletaInscripcionInputSerializer,
    AtletaInscripcionResponseSerializer,
    get_user_module_token,
)
from ..permissions import IsEntrenadorOrEstudianteVinculacion

logger = logging.getLogger(__name__)


class InscripcionController(viewsets.ViewSet):
    """
    Controlador para gestionar las Inscripciones de los atletas.
    """

    permission_classes = [IsEntrenadorOrEstudianteVinculacion]
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
        """Crea un atleta y su inscripción directamente."""
        token = get_user_module_token()
        payload = request.data
        persona_data = payload.get("persona")
        atleta_data = payload.get("atleta")
        inscripcion_data = payload.get("inscripcion")

        try:
            result = self.service.create_atleta_inscripcion(
                persona_data, atleta_data, inscripcion_data, token
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.error(f"Error en create inscripcion: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
        """Actualiza los datos de la persona, atleta e inscripción."""
        token = get_user_module_token()
        payload = request.data
        persona_data = payload.get("persona")
        atleta_data = payload.get("atleta")
        inscripcion_data = payload.get("inscripcion")

        try:
            result = self.service.update_atleta_inscripcion(
                pk, persona_data, atleta_data, inscripcion_data, token
            )
            if not result:
                return Response(
                    {"error": "Inscripción no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en update inscripcion: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
