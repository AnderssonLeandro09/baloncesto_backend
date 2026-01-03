"""Controlador para Prueba Física."""

import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.prueba_fisica_service import PruebaFisicaService
from ..serializers import (
    PruebaFisicaSerializer,
    PruebaFisicaInputSerializer,
    PruebaFisicaResponseSerializer,
)
from ..permissions import IsEntrenadorOrEstudianteVinculacion

logger = logging.getLogger(__name__)


class PruebaFisicaController(viewsets.ViewSet):
    """Controlador para gestionar las pruebas físicas de los atletas."""

    permission_classes = [IsEntrenadorOrEstudianteVinculacion]
    service = PruebaFisicaService()

    @extend_schema(responses={200: PruebaFisicaResponseSerializer(many=True)})
    def list(self, request):
        """Lista todas las pruebas físicas."""
        try:
            pruebas = self.service.get_all_pruebas_fisicas()
            serializer = PruebaFisicaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en list pruebas físicas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaFisicaInputSerializer,
        responses={201: PruebaFisicaResponseSerializer},
    )
    def create(self, request):
        """Crea una nueva prueba física."""
        serializer = PruebaFisicaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.create_prueba_fisica(serializer.validated_data)
            response_serializer = PruebaFisicaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en create prueba física: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene una prueba física por ID."""
        try:
            prueba = self.service.get_prueba_fisica_by_id(pk)
            if not prueba:
                return Response(
                    {"error": "Prueba física no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = PruebaFisicaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en retrieve prueba física: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaFisicaInputSerializer,
        responses={200: PruebaFisicaResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza una prueba física existente."""
        serializer = PruebaFisicaInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.update_prueba_fisica(pk, serializer.validated_data)
            response_serializer = PruebaFisicaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en update prueba física: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer})
    @action(detail=True, methods=["patch"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        """Cambia el estado de la prueba física."""
        try:
            prueba = self.service.toggle_estado(pk)
            serializer = PruebaFisicaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en toggle_estado prueba física: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="atleta/(?P<atleta_id>[^/.]+)")
    def by_atleta(self, request, atleta_id=None):
        """Obtiene todas las pruebas físicas de un atleta específico."""
        try:
            pruebas = self.service.get_pruebas_by_atleta(atleta_id)
            serializer = PruebaFisicaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en by_atleta pruebas físicas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
