"""Controlador para el Perfil de Usuario."""

import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from ..permissions import IsAdminOrEntrenadorOrEstudiante
from ..serializers import (
    ProfileResponseSerializer,
    get_user_module_token,
)
from ..services.profile_service import ProfileService

logger = logging.getLogger(__name__)


class ProfileController(viewsets.ViewSet):
    """Maneja el perfil del usuario autenticado."""

    permission_classes = [IsAdminOrEntrenadorOrEstudiante]
    service = ProfileService()

    @extend_schema(responses={200: ProfileResponseSerializer})
    @action(detail=False, methods=["get"])
    def me(self, request):
        """Obtiene la información del perfil del usuario actual."""
        token = get_user_module_token()
        if not token:
            return Response(
                {
                    "error": "No se pudo establecer comunicación con el servicio de usuarios"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            data = self.service.get_profile_data(request.user, token)
            if not data:
                return Response(
                    {"error": "Perfil no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
