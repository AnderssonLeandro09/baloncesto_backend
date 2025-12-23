"""Controlador para la gestión de Grupos de Atletas."""

from rest_framework import status, viewsets, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter
from ..permissions import IsAdminOrEntrenador
from ..serializers import (
    GrupoAtletaSerializer, 
    GrupoAtletaResponseSerializer
)
from ..services.grupo_atleta_service import GrupoAtletaService


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
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
                min_edad=int(min_edad) if min_edad else None,
                max_edad=int(max_edad) if max_edad else None
            )
            ids = [atleta.id for atleta in data]
            return Response(ids, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: serializers.ListField(child=serializers.IntegerField())})
    @action(detail=True, methods=["get"], url_path="atletas-elegibles")
    def atletas_elegibles_grupo(self, request, pk=None):
        """Lista IDs de atletas elegibles para un grupo específico (que no estén ya en él)."""
        try:
            data = self.service.list_atletas_elegibles(grupo_id=pk)
            ids = [atleta.id for atleta in data]
            return Response(ids, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=GrupoAtletaSerializer,
        responses={201: GrupoAtletaResponseSerializer},
    )
    def create(self, request):
        """Crea un nuevo grupo de atletas."""
        try:
            grupo = self.service.create_grupo(request.data)
            serializer = GrupoAtletaResponseSerializer(grupo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
