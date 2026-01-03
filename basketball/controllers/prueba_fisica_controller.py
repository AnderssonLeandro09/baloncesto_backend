"""Controlador para Prueba Física."""

import logging
from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.prueba_fisica_service import PruebaFisicaService
from ..serializers import (
    PruebaFisicaSerializer,
    PruebaFisicaInputSerializer,
    PruebaFisicaResponseSerializer,
    get_user_module_token,
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
        token = get_user_module_token()
        try:
            pruebas = self.service.get_all_pruebas_fisicas_completas(token, user=request.user)
            serializer = PruebaFisicaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en list pruebas físicas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: serializers.ListField(child=serializers.DictField())})
    @action(detail=False, methods=["get"], url_path="atletas-habilitados")
    def atletas_habilitados(self, request):
        """Obtiene la lista de atletas con inscripción habilitada."""
        token = get_user_module_token()
        try:
            atletas = self.service.get_atletas_habilitados_con_persona(token, user=request.user)
            return Response(atletas, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en atletas_habilitados: {exc}")
            return Response(
                {"error": "Error al obtener atletas habilitados"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaFisicaInputSerializer,
        responses={201: PruebaFisicaResponseSerializer},
    )
    def create(self, request):
        """Crea una nueva prueba física."""
        token = get_user_module_token()
        serializer = PruebaFisicaInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.create_prueba_fisica(serializer.validated_data, user=request.user)
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(prueba.id, token, user=request.user)
            response_serializer = PruebaFisicaResponseSerializer(prueba_completa)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as exc:
            logger.error(f"Error en create prueba física: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene una prueba física por ID."""
        token = get_user_module_token()
        
        # Validar que pk sea un entero válido
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            prueba = self.service.get_prueba_fisica_completa(pk, token, user=request.user)
            if not prueba:
                return Response(
                    {"error": "Prueba física no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = PruebaFisicaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
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
        token = get_user_module_token()
        
        # Validar que pk sea un entero válido
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = PruebaFisicaInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.update_prueba_fisica(pk, serializer.validated_data, user=request.user)
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(prueba.id, token, user=request.user)
            response_serializer = PruebaFisicaResponseSerializer(prueba_completa)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
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
        token = get_user_module_token()
        
        # Validar que pk sea un entero válido
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return Response(
                {"error": "ID inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            prueba = self.service.toggle_estado(pk, user=request.user)
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(prueba.id, token, user=request.user)
            serializer = PruebaFisicaResponseSerializer(prueba_completa)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
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
        token = get_user_module_token()
        try:
            pruebas = self.service.get_pruebas_by_atleta_completas(atleta_id, token, user=request.user)
            serializer = PruebaFisicaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en by_atleta pruebas físicas: {exc}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
