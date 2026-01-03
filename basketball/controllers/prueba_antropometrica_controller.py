"""Controlador para Prueba Antropométrica."""

import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.prueba_antropometrica_service import PruebaAntropometricaService
from ..serializers import (
    PruebaAntropometricaSerializer,
    PruebaAntropometricaInputSerializer,
    PruebaAntropometricaResponseSerializer,
)
from ..permissions import IsEntrenadorOrEstudianteVinculacion

logger = logging.getLogger(__name__)


class PruebaAntropometricaController(viewsets.ViewSet):
    """Controlador para gestionar las pruebas antropométricas de los atletas."""

    permission_classes = [IsEntrenadorOrEstudianteVinculacion]
    service = PruebaAntropometricaService()

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer(many=True)})
    def list(self, request):
        """Lista todas las pruebas antropométricas."""
        try:
            pruebas = self.service.get_all_pruebas_antropometricas()
            serializer = PruebaAntropometricaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en list pruebas antropométricas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaAntropometricaInputSerializer,
        responses={201: PruebaAntropometricaResponseSerializer},
    )
    def create(self, request):
        """Crea una nueva prueba antropométrica."""
        serializer = PruebaAntropometricaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.create_prueba_antropometrica(
                serializer.validated_data,
                request.user,
            )
            response_serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en create prueba antropométrica: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene una prueba antropométrica por ID."""
        try:
            prueba = self.service.get_prueba_antropometrica_by_id(pk)
            if not prueba:
                return Response(
                    {"error": "Prueba antropométrica no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en retrieve prueba antropométrica: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaAntropometricaInputSerializer,
        responses={200: PruebaAntropometricaResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza una prueba antropométrica existente."""
        serializer = PruebaAntropometricaInputSerializer(
            data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.update_prueba_antropometrica(
                pk,
                serializer.validated_data,
                request.user,
            )
            response_serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en update prueba antropométrica: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer})
    @action(detail=True, methods=["patch"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        """Cambia el estado de la prueba antropométrica."""
        try:
            prueba = self.service.toggle_estado(pk)
            serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en toggle_estado prueba antropométrica: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="atleta/(?P<atleta_id>[^/.]+)")
    def by_atleta(self, request, atleta_id=None):
        """Obtiene todas las pruebas antropométricas de un atleta específico."""
        try:
            pruebas = self.service.get_pruebas_antropometricas_by_atleta(atleta_id)
            serializer = PruebaAntropometricaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en by_atleta pruebas antropométricas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
