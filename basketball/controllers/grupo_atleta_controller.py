"""Controlador para la gestión de Grupos de Atletas."""

import logging
from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ..permissions import IsAdminOrEntrenador
from ..serializers import (
    GrupoAtletaSerializer, 
    GrupoAtletaResponseSerializer
)
from ..services.grupo_atleta_service import GrupoAtletaService

logger = logging.getLogger(__name__)


class GrupoAtletaController(viewsets.ViewSet):
    """CRUD para la gestión de grupos de atletas."""

    permission_classes = [IsAdminOrEntrenador]
    serializer_class = GrupoAtletaSerializer
    service = GrupoAtletaService()

    @extend_schema(responses={200: GrupoAtletaResponseSerializer(many=True)})
    def list(self, request):
        """Lista todos los grupos de atletas activos."""
        try:
            data = self.service.list_grupos()
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
            min_edad_str = request.query_params.get("min_edad")
            max_edad_str = request.query_params.get("max_edad")
            
            # Validar conversión segura a enteros
            min_edad = None
            max_edad = None
            
            if min_edad_str:
                try:
                    min_edad = int(min_edad_str)
                    if min_edad < 0 or min_edad > 150:
                        return Response(
                            {"error": "Edad mínima debe estar entre 0 y 150"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except ValueError:
                    return Response(
                        {"error": "Edad mínima debe ser un número válido"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if max_edad_str:
                try:
                    max_edad = int(max_edad_str)
                    if max_edad < 0 or max_edad > 150:
                        return Response(
                            {"error": "Edad máxima debe estar entre 0 y 150"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except ValueError:
                    return Response(
                        {"error": "Edad máxima debe ser un número válido"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
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
            logger.warning(f"Validation error en atletas elegibles grupo {pk}: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en atletas elegibles grupo {pk}: {exc}")
            return Response({"error": "Error al obtener atletas elegibles"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(responses={200: GrupoAtletaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene un grupo de atletas por su ID."""
        try:
            grupo = self.service.get_grupo(pk)
            if not grupo:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = GrupoAtletaResponseSerializer(grupo)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en retrieve grupo {pk}: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en retrieve grupo {pk}: {exc}")
            return Response({"error": "Error al obtener el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={201: GrupoAtletaResponseSerializer},
    )
    def create(self, request):
        """Crea un nuevo grupo de atletas."""
        try:
            grupo = self.service.create_grupo(request.data)
            serializer = GrupoAtletaResponseSerializer(grupo)
            logger.info(f"Grupo creado exitosamente: {grupo.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            logger.warning(f"Validation error en create grupo: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en create grupo: {exc}")
            return Response({"error": "Error al crear el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={200: GrupoAtletaResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza un grupo de atletas existente."""
        try:
            grupo = self.service.update_grupo(pk, request.data)
            if not grupo:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = GrupoAtletaResponseSerializer(grupo)
            logger.info(f"Grupo actualizado exitosamente: {pk}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            logger.warning(f"Validation error en update grupo {pk}: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en update grupo {pk}: {exc}")
            return Response({"error": "Error al actualizar el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={200: GrupoAtletaResponseSerializer},
    )
    def partial_update(self, request, pk=None):
        """Actualización parcial de un grupo de atletas."""
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        """Da de baja (eliminación lógica) un grupo de atletas."""
        try:
            success = self.service.delete_grupo(pk)
            if not success:
                return Response(
                    {"error": "Grupo no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            logger.info(f"Grupo eliminado (lógicamente) exitosamente: {pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as exc:
            logger.warning(f"Validation error en delete grupo {pk}: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(f"Error inesperado en delete grupo {pk}: {exc}")
            return Response({"error": "Error al eliminar el grupo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
