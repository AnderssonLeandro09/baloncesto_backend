"""Controlador para Prueba Antropométrica."""

import logging
from typing import Any, Dict, Optional
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..constants import ErrorMessages
from ..services.prueba_antropometrica_service import PruebaAntropometricaService
from ..serializers import (
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
    def list(self, request: Request) -> Response:
        """Lista todas las pruebas antropométricas con filtros y paginación."""
        try:
            # Obtener parámetros de filtrado y paginación
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('pageSize', 10))
            atleta_id = request.query_params.get('atleta')
            estado = request.query_params.get('estado')
            fecha_inicio = request.query_params.get('fecha_inicio')
            fecha_fin = request.query_params.get('fecha_fin')
            
            # Construir filtros
            filtros = {}
            if atleta_id:
                filtros['atleta_id'] = int(atleta_id)
            if estado is not None and estado != '':
                filtros['estado'] = estado.lower() == 'true'
            if fecha_inicio:
                filtros['fecha_inicio'] = fecha_inicio
            if fecha_fin:
                filtros['fecha_fin'] = fecha_fin
                
            pruebas, total = self.service.get_all_pruebas_antropometricas(
                page=page,
                page_size=page_size,
                **filtros
            )
            serializer = PruebaAntropometricaResponseSerializer(pruebas, many=True)
            
            return Response({
                'results': serializer.data,
                'count': total,
                'page': page,
                'page_size': page_size
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en list pruebas antropométricas: {exc}")
            return Response(
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaAntropometricaInputSerializer,
        responses={201: PruebaAntropometricaResponseSerializer},
    )
    def create(self, request: Request) -> Response:
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
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer})
    def retrieve(self, request: Request, pk: Optional[int] = None) -> Response:
        """Obtiene una prueba antropométrica por ID."""
        try:
            prueba = self.service.get_prueba_antropometrica_by_id(pk)
            if not prueba:
                return Response(
                    {"error": ErrorMessages.PRUEBA_ANTROPOMETRICA_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en retrieve prueba antropométrica: {exc}")
            return Response(
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaAntropometricaInputSerializer,
        responses={200: PruebaAntropometricaResponseSerializer},
    )
    def update(self, request: Request, pk: Optional[int] = None) -> Response:
        """Actualiza una prueba antropométrica existente (PUT - completo)."""
        serializer = PruebaAntropometricaInputSerializer(
            data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.update_prueba_antropometrica(
                pk,
                serializer.validated_data,
            )
            response_serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en update prueba antropométrica: {exc}")
            return Response(
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaAntropometricaInputSerializer,
        responses={200: PruebaAntropometricaResponseSerializer},
    )
    def partial_update(self, request: Request, pk: Optional[int] = None) -> Response:
        """Actualiza parcialmente una prueba antropométrica (PATCH)."""
        serializer = PruebaAntropometricaInputSerializer(
            data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.update_prueba_antropometrica(
                pk,
                serializer.validated_data,
            )
            response_serializer = PruebaAntropometricaResponseSerializer(prueba)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error en partial_update prueba antropométrica: {exc}")
            return Response(
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer})
    @action(detail=True, methods=["patch"], url_path="toggle-estado")
    def toggle_estado(self, request: Request, pk: Optional[int] = None) -> Response:
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
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="atleta/(?P<atleta_id>[^/.]+)")
    def by_atleta(self, request: Request, atleta_id: Optional[int] = None) -> Response:
        """Obtiene todas las pruebas antropométricas de un atleta específico."""
        try:
            pruebas = self.service.get_pruebas_antropometricas_by_atleta(atleta_id)
            serializer = PruebaAntropometricaResponseSerializer(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Error en by_atleta pruebas antropométricas: {exc}")
            return Response(
                {"error": ErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
