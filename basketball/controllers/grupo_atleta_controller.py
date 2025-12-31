"""Controlador para la gestión de Grupos de Atletas."""

import logging
from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ..permissions import IsEntrenador
from ..serializers import (
    GrupoAtletaSerializer, 
    GrupoAtletaResponseSerializer
)
from ..services.grupo_atleta_service import GrupoAtletaService

logger = logging.getLogger(__name__)


class GrupoAtletaController(viewsets.ViewSet):
    """CRUD para la gestión de grupos de atletas, solo para entrenadores"""

    permission_classes = [IsEntrenador]
    serializer_class = GrupoAtletaSerializer
    service = GrupoAtletaService()

    @extend_schema(responses={200: GrupoAtletaResponseSerializer(many=True)})
    def list(self, request):
        """Lista los grupos del entrenador autenticado.       

        Cada entrenador ve únicamente sus propios grupos.
        """
        try:
            data = self.service.list_grupos_by_user(request.user)
            serializer = GrupoAtletaResponseSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en list grupos: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en list grupos: {exc}")
            return Response({"error": "Error al listar grupos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        parameters=[
            OpenApiParameter("min_edad", type=int, description="Edad mínima"),
            OpenApiParameter("max_edad", type=int, description="Edad máxima"),
        ],
        responses={200: serializers.ListField(child=serializers.IntegerField())}
    )
    @action(detail=False, methods=["get"], url_path="atletas-elegibles")
    def atletas_elegibles_general(self, request):
        """Lista IDs de atletas elegibles basados en un rango de edad."""
        try:
            min_edad = request.query_params.get("min_edad")
            max_edad = request.query_params.get("max_edad")
            
            data = self.service.list_atletas_elegibles(
                min_edad=min_edad,
                max_edad=max_edad
            )
            ids = [atleta.id for atleta in data]
            return Response(ids, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en atletas elegibles: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en atletas elegibles: {exc}")
            return Response({"error": "Error al obtener atletas elegibles"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={200: serializers.ListField(child=serializers.IntegerField())})
    @action(detail=True, methods=["get"], url_path="atletas-elegibles")
    def atletas_elegibles_grupo(self, request, pk=None):
        """Lista IDs de atletas elegibles para un grupo específico (que no estén ya en él)."""
        try:
            data = self.service.list_atletas_elegibles(grupo_id=pk)
            ids = [atleta.id for atleta in data]
            return Response(ids, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en atletas elegibles grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en atletas elegibles grupo: {exc}")
            return Response({"error": "Error al obtener atletas elegibles"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={200: GrupoAtletaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene un grupo de atletas por su ID.
        
        Solo el entrenador dueño del grupo puede acceder.
        """
        try:
            grupo = self.service.get_grupo(pk, user=request.user)
            if not grupo:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            serializer = GrupoAtletaResponseSerializer(grupo)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en retrieve grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en retrieve grupo: {exc}")
            return Response({"error": "Error al obtener el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={201: GrupoAtletaResponseSerializer},
    )
    def create(self, request):
        """Crea un nuevo grupo de atletas.
        
        El entrenador se asigna automáticamente desde el usuario autenticado.
        """
        try:
            # Validar datos con serializer antes de pasar al service
            serializer = GrupoAtletaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Pasar datos validados al service
            grupo = self.service.create_grupo(serializer.validated_data, user=request.user)
            response_serializer = GrupoAtletaResponseSerializer(grupo)
            logger.info(f"Grupo creado exitosamente: {grupo.id} por usuario {request.user.pk}")
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as exc:
            logger.warning(f"Serializer validation error en create grupo: {exc}")
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            logger.warning(f"Service validation error en create grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en create grupo: {exc}")
            return Response({"error": "Error al crear el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={200: GrupoAtletaResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza un grupo de atletas existente.
        
        Solo el entrenador dueño del grupo puede actualizarlo.
        """
        try:
            # Validar datos con serializer (partial para PATCH)
            serializer = GrupoAtletaSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            grupo = self.service.update_grupo(pk, serializer.validated_data, user=request.user)
            if not grupo:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            response_serializer = GrupoAtletaResponseSerializer(grupo)
            logger.info(f"Grupo actualizado exitosamente por usuario {request.user.pk}")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as exc:
            logger.warning(f"Serializer validation error en update grupo: {exc}")
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            logger.warning(f"Service validation error en update grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en update grupo: {exc}")
            return Response({"error": "Error al actualizar el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={200: GrupoAtletaResponseSerializer},
    )
    def partial_update(self, request, pk=None):
        """Actualización parcial de un grupo de atletas."""
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """Da de baja (eliminación lógica) un grupo de atletas.
        
        Solo el entrenador dueño del grupo puede eliminarlo.
        """
        try:
            success = self.service.delete_grupo(pk, user=request.user)
            if not success:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            logger.info(f"Grupo eliminado (lógicamente) exitosamente por usuario {request.user.pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as exc:
            logger.warning(f"Validation error en delete grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en delete grupo: {exc}")
            return Response({"error": "Error al eliminar el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
