"""Controlador para Entrenador."""

from rest_framework import status, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..permissions import IsAdmin
from ..serializers import (
    EntrenadorSerializer,
    EntrenadorInputSerializer,
    EntrenadorResponseSerializer,
    get_user_module_token,
)
from ..services.entrenador_service import (
    EntrenadorService,
)


class EntrenadorController(viewsets.ViewSet):
    """CRUD para entrenadores."""

    permission_classes = [IsAdmin]
    # serializer_class se usa por defecto, pero extend_schema lo sobreescribe
    serializer_class = EntrenadorSerializer
    service = EntrenadorService()

    @extend_schema(responses={200: EntrenadorResponseSerializer(many=True)})
    def list(self, request):
        # Usar token de admin para consultar el módulo de usuarios
        token = get_user_module_token()
        try:
            data = self.service.list_entrenadores(token)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: EntrenadorResponseSerializer})
    def retrieve(self, request, pk=None):
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
        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, "dict") else request.data
        persona_data = payload.get("persona") or payload.get("persona_data")
        entrenador_data = (
            payload.get("entrenador") or payload.get("entrenador_data") or {}
        )
        try:
            result = self.service.create_entrenador(
                persona_data or {}, entrenador_data, token
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={200: EntrenadorResponseSerializer},
    )
    def update(self, request, pk=None):
        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, "dict") else request.data
        persona_data = payload.get("persona") or payload.get("persona_data")
        entrenador_data = (
            payload.get("entrenador") or payload.get("entrenador_data") or {}
        )
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
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={204: None})
    def destroy(self, request, pk=None):
        try:
            success = self.service.delete_entrenador(pk)
            if not success:
                return Response(
                    {"error": "Entrenador no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
