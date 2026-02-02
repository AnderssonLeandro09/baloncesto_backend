"""Controlador para Entrenador."""

from typing import Any, Dict, Optional
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema

from ..constants import ErrorMessages
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
    def list(self, request: Request) -> Response:
        """Lista todos los entrenadores activos."""
        token = get_user_module_token()
        try:
            data = self.service.list_entrenadores(token)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: EntrenadorResponseSerializer})
    def retrieve(self, request: Request, pk: Optional[int] = None) -> Response:
        """Obtiene un entrenador por su ID."""
        token = get_user_module_token()
        try:
            data = self.service.get_entrenador(pk, token)
            if not data:
                return Response(
                    {"error": ErrorMessages.ENTRENADOR_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={201: EntrenadorResponseSerializer},
    )
    def create(self, request: Request) -> Response:
        """Crea un nuevo entrenador."""
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
    def update(self, request: Request, pk: Optional[int] = None) -> Response:
        """Actualiza un entrenador existente."""
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
                    {"error": ErrorMessages.ENTRENADOR_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EntrenadorInputSerializer,
        responses={200: EntrenadorResponseSerializer},
    )
    def partial_update(self, request: Request, pk: Optional[int] = None) -> Response:
        """Actualización parcial de un entrenador."""
        return self.update(request, pk)

    def destroy(self, request: Request, pk: Optional[int] = None) -> Response:
        """Da de baja (eliminación lógica) un entrenador."""
        success = self.service.delete_entrenador(pk)
        if not success:
            return Response(
                {"error": ErrorMessages.ENTRENADOR_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
