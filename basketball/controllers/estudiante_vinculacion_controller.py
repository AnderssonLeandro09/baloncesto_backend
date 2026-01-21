"""Controlador para Estudiante de Vinculación."""

from rest_framework import status, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..permissions import IsAdmin
from ..serializers import (
    EstudianteVinculacionSerializer,
    EstudianteVinculacionInputSerializer,
    EstudianteVinculacionResponseSerializer,
    get_user_module_token,
)
from ..services.estudiante_vinculacion_service import (
    EstudianteVinculacionService,
)


class EstudianteVinculacionController(viewsets.ViewSet):
    """CRUD para estudiantes de vinculación."""

    permission_classes = [IsAdmin]
    # serializer_class se usa por defecto, pero extend_schema lo sobreescribe
    serializer_class = EstudianteVinculacionSerializer
    service = EstudianteVinculacionService()

    @extend_schema(responses={200: EstudianteVinculacionResponseSerializer(many=True)})
    def list(self, request):
        # Usar token de admin para consultar el módulo de usuarios
        token = get_user_module_token()
        try:
            data = self.service.list_estudiantes(token)
            return Response({
                "msg": "Estudiantes listados correctamente",
                "data": data,
                "code": status.HTTP_200_OK,
                "status": "success"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "msg": "Error al listar estudiantes",
                "data": str(exc),
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: EstudianteVinculacionResponseSerializer})
    def retrieve(self, request, pk=None):
        token = get_user_module_token()
        try:
            data = self.service.get_estudiante(pk, token)
            if not data:
                return Response({
                    "msg": "Estudiante no encontrado",
                    "data": None,
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "error"
                }, status=status.HTTP_404_NOT_FOUND)
            return Response({
                "msg": "Estudiante obtenido correctamente",
                "data": data,
                "code": status.HTTP_200_OK,
                "status": "success"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "msg": "Error al obtener estudiante",
                "data": str(exc),
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EstudianteVinculacionInputSerializer,
        responses={201: EstudianteVinculacionResponseSerializer},
    )
    def create(self, request):
        token = get_user_module_token()
        
        # Validar datos usando el serializer
        serializer = EstudianteVinculacionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "msg": "Error de validación",
                "data": serializer.errors,
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        validated_data = serializer.validated_data
        persona_data = validated_data.get("persona")
        estudiante_data = validated_data.get("estudiante")
        
        try:
            result = self.service.create_estudiante(
                persona_data, estudiante_data, token
            )
            return Response({
                "msg": "Estudiante creado correctamente",
                "data": result,
                "code": status.HTTP_201_CREATED,
                "status": "success"
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({
                "msg": "Error al crear estudiante",
                "data": str(exc),
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EstudianteVinculacionInputSerializer,
        responses={200: EstudianteVinculacionResponseSerializer},
    )
    def update(self, request, pk=None):
        token = get_user_module_token()
        
        # Validar datos usando el serializer (permitiendo actualización parcial si es necesario)
        serializer = EstudianteVinculacionInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "msg": "Error de validación",
                "data": serializer.errors,
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        validated_data = serializer.validated_data
        persona_data = validated_data.get("persona")
        estudiante_data = validated_data.get("estudiante")
        
        try:
            result = self.service.update_estudiante(
                pk, persona_data or {}, estudiante_data or {}, token
            )
            if not result:
                return Response({
                    "msg": "Estudiante no encontrado",
                    "data": None,
                    "code": status.HTTP_404_NOT_FOUND,
                    "status": "error"
                }, status=status.HTTP_404_NOT_FOUND)
            return Response({
                "msg": "Estudiante actualizado correctamente",
                "data": result,
                "code": status.HTTP_200_OK,
                "status": "success"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({
                "msg": "Error al actualizar estudiante",
                "data": str(exc),
                "code": status.HTTP_400_BAD_REQUEST,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=EstudianteVinculacionInputSerializer,
        responses={200: EstudianteVinculacionResponseSerializer},
    )
    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        success = self.service.delete_estudiante(pk)
        if not success:
            return Response({
                "msg": "Estudiante no encontrado",
                "data": None,
                "code": status.HTTP_404_NOT_FOUND,
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "msg": "Estudiante eliminado correctamente",
            "data": None,
            "code": status.HTTP_200_OK,
            "status": "success"
        }, status=status.HTTP_200_OK)
