"""Controlador para Entrenador."""

from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from ..permissions import IsAdmin
from ..serializers import (
    EntrenadorSerializer,
    EntrenadorInputSerializer,
    EntrenadorResponseSerializer,
    get_user_module_token,
)
from ..services.entrenador_service import EntrenadorService


class EntrenadorController(viewsets.ViewSet):
    """CRUD para entrenadores."""

    permission_classes = [IsAdmin]
    serializer_class = EntrenadorSerializer
    service = EntrenadorService()

    @extend_schema(responses={200: EntrenadorResponseSerializer(many=True)})
    def list(self, request):
        """Lista todos los entrenadores activos."""
        token = get_user_module_token()
        try:
            data = self.service.list_entrenadores(token)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: EntrenadorResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene un entrenador por su ID."""
        token = get_user_module_token()
        try:
            data = self.service.get_entrenador(pk, token)
            if not data:
                return Response(
                    {"error": "Entrenador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={201: EntrenadorResponseSerializer},
    )
    def create(self, request):
        """Crea un nuevo entrenador."""
        import logging

        logger = logging.getLogger(__name__)

        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, "dict") else request.data

        logger.info(f"=== CREATE ENTRENADOR - Payload recibido ===")
        logger.info(f"Payload completo: {payload}")

        persona_data = payload.get("persona") or payload.get("persona_data")
        entrenador_data = (
            payload.get("entrenador") or payload.get("entrenador_data") or {}
        )

        logger.info(f"persona_data: {persona_data}")
        logger.info(f"entrenador_data: {entrenador_data}")

        # Validar con serializer antes de enviar al servicio (solo si hay datos completos)
        # Si no hay persona_data o entrenador_data, dejar que el servicio lo maneje
        if persona_data and entrenador_data:
            serializer = EntrenadorInputSerializer(data=payload)
            if not serializer.is_valid():
                logger.error(
                    f"Errores de validación del serializer: {serializer.errors}"
                )
                return Response(
                    {
                        "error": "Error de validacion de datos",
                        "details": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            result = self.service.create_entrenador(
                persona_data or {}, entrenador_data, token
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as exc:
            # Manejar errores de validación del serializer
            logger.error(f"ValidationError: {exc}")
            error_detail = exc.detail if hasattr(exc, "detail") else str(exc)
            if isinstance(error_detail, list):
                error_msg = " | ".join(str(e) for e in error_detail)
            else:
                error_msg = str(error_detail)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Exception: {exc}", exc_info=True)
            error_msg = str(exc)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={200: EntrenadorResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza un entrenador existente (PUT - requiere todos los datos)."""
        import logging

        logger = logging.getLogger(__name__)

        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, "dict") else request.data

        logger.info(f"=== UPDATE ENTRENADOR (PUT) - Payload recibido ===")
        logger.info(f"Payload completo: {payload}")

        persona_data = payload.get("persona") or payload.get("persona_data")
        entrenador_data = (
            payload.get("entrenador") or payload.get("entrenador_data") or {}
        )

        logger.info(f"persona_data: {persona_data}")
        logger.info(f"entrenador_data: {entrenador_data}")

        try:
            result = self.service.update_entrenador(
                pk, persona_data or {}, entrenador_data, token
            )
            if not result:
                return Response(
                    {"error": "Entrenador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)
        except serializers.ValidationError as exc:
            logger.error(f"ValidationError: {exc}")
            error_detail = exc.detail if hasattr(exc, "detail") else str(exc)
            if isinstance(error_detail, list):
                error_msg = " | ".join(str(e) for e in error_detail)
            else:
                error_msg = str(error_detail)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Exception: {exc}", exc_info=True)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={200: EntrenadorResponseSerializer},
    )
    def partial_update(self, request, pk=None):
        """Actualización parcial de un entrenador (PATCH - permite actualizar campos individuales)."""
        import logging

        logger = logging.getLogger(__name__)

        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, "dict") else request.data

        logger.info(f"=== PARTIAL UPDATE ENTRENADOR (PATCH) - Payload recibido ===")
        logger.info(f"Payload completo: {payload}")

        persona_data = payload.get("persona") or payload.get("persona_data")
        entrenador_data = (
            payload.get("entrenador") or payload.get("entrenador_data") or {}
        )

        logger.info(f"persona_data: {persona_data}")
        logger.info(f"entrenador_data: {entrenador_data}")

        try:
            result = self.service.update_entrenador(
                pk, persona_data or {}, entrenador_data, token
            )
            if not result:
                return Response(
                    {"error": "Entrenador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)
        except serializers.ValidationError as exc:
            logger.error(f"ValidationError: {exc}")
            error_detail = exc.detail if hasattr(exc, "detail") else str(exc)
            if isinstance(error_detail, list):
                error_msg = " | ".join(str(e) for e in error_detail)
            else:
                error_msg = str(error_detail)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Exception: {exc}", exc_info=True)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: EntrenadorResponseSerializer})
    @action(detail=True, methods=["patch"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        """Activa o desactiva un entrenador (eliminación lógica reversible)."""
        token = get_user_module_token()
        try:
            result = self.service.toggle_estado(pk, token)
            if not result:
                return Response(
                    {"error": "Entrenador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Da de baja (eliminación lógica) un entrenador."""
        success = self.service.delete_entrenador(pk)
        if not success:
            return Response(
                {"error": "Entrenador no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
