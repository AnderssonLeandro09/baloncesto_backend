"""Controlador para Administrador."""

import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.administrador_service import AdministradorService
from ..serializers import (
    AdministradorSerializer,
    AdministradorInputSerializer,
    AdministradorResponseSerializer,
    get_user_module_token
)
from ..permissions import IsAdmin

logger = logging.getLogger(__name__)


class AdministradorController(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    serializer_class = AdministradorSerializer
    service = AdministradorService()

    @extend_schema(
        responses={200: AdministradorResponseSerializer(many=True)}
    )
    def list(self, request):
        token = get_user_module_token()
        try:
            data = self.service.get_all_administradores(token)
            return Response(data, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error interno en list administradores: {exc}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=AdministradorInputSerializer,
        responses={201: AdministradorResponseSerializer}
    )
    def create(self, request):
        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
        persona_data = payload.get('persona') or payload.get('persona_data')
        administrador_data = payload.get('administrador') or payload.get('administrador_data') or {}
        try:
            result = self.service.create_administrador(persona_data or {}, administrador_data, token)
            return Response(result, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error interno en create administrador: {exc}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        responses={200: AdministradorResponseSerializer}
    )
    def retrieve(self, request, pk=None):
        token = get_user_module_token()
        try:
            data = self.service.get_administrador_by_id(pk, token)
            if not data:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response(data, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error interno en retrieve administrador: {exc}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=AdministradorInputSerializer,
        responses={200: AdministradorResponseSerializer}
    )
    def update(self, request, pk=None):
        token = get_user_module_token()
        payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
        persona_data = payload.get('persona') or payload.get('persona_data')
        administrador_data = payload.get('administrador') or payload.get('administrador_data') or {}
        try:
            result = self.service.update_administrador(pk, persona_data or {}, administrador_data, token)
            if not result:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error interno en update administrador: {exc}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        responses={204: None}
    )
    def destroy(self, request, pk=None):
        try:
            success = self.service.delete_administrador(pk)
            if not success:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            logger.error(f"Error interno en destroy administrador: {exc}")
            return Response({'error': 'Error interno del servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
