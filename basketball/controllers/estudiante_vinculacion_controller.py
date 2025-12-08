"""
Controlador para EstudianteVinculacion

Implementa los endpoints CRUD para estudiantes de vinculación
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from basketball.controllers.base_controller import BaseController
from basketball.services.estudiante_vinculacion_service import EstudianteVinculacionService


# =============================================================================
# Serializers para documentación de Swagger
# =============================================================================

class EstudianteVinculacionInputSerializer(serializers.Serializer):
    """Serializer para crear estudiante de vinculación"""
    nombre = serializers.CharField(max_length=100, help_text="Nombre del estudiante")
    apellido = serializers.CharField(max_length=100, help_text="Apellido del estudiante")
    email = serializers.EmailField(help_text="Correo institucional (@unl.edu.ec)")
    dni = serializers.CharField(max_length=10, help_text="Cédula de identidad (10 dígitos)")
    clave = serializers.CharField(max_length=255, help_text="Contraseña del estudiante")
    carrera = serializers.CharField(max_length=100, help_text="Carrera del estudiante")
    semestre = serializers.CharField(max_length=20, help_text="Semestre actual (1-10)")
    foto_perfil = serializers.CharField(max_length=255, required=False, help_text="URL de foto de perfil")


class EstudianteVinculacionUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar estudiante de vinculación"""
    nombre = serializers.CharField(max_length=100, required=False, help_text="Nombre del estudiante")
    apellido = serializers.CharField(max_length=100, required=False, help_text="Apellido del estudiante")
    email = serializers.EmailField(required=False, help_text="Correo institucional (@unl.edu.ec)")
    carrera = serializers.CharField(max_length=100, required=False, help_text="Carrera del estudiante")
    semestre = serializers.CharField(max_length=20, required=False, help_text="Semestre actual (1-10)")
    foto_perfil = serializers.CharField(max_length=255, required=False, help_text="URL de foto de perfil")


class EstudianteVinculacionOutputSerializer(serializers.Serializer):
    """Serializer para respuesta de estudiante de vinculación"""
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    dni = serializers.CharField()
    foto_perfil = serializers.CharField(allow_null=True)
    rol = serializers.CharField()
    estado = serializers.BooleanField()
    fecha_registro = serializers.CharField(allow_null=True)
    carrera = serializers.CharField()
    semestre = serializers.CharField()


class ServiceResultSerializer(serializers.Serializer):
    """Serializer genérico para respuestas del servicio"""
    status = serializers.CharField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class ServiceResultListSerializer(serializers.Serializer):
    """Serializer para respuestas con lista de estudiantes"""
    status = serializers.CharField()
    message = serializers.CharField()
    data = EstudianteVinculacionOutputSerializer(many=True, required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class ServiceResultDetailSerializer(serializers.Serializer):
    """Serializer para respuestas con un estudiante"""
    status = serializers.CharField()
    message = serializers.CharField()
    data = EstudianteVinculacionOutputSerializer(required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)


# =============================================================================
# Controllers
# =============================================================================

class EstudianteVinculacionListController(BaseController):
    """
    Controlador para listar y crear estudiantes de vinculación.
    
    GET: Lista todos los estudiantes activos
    POST: Crea un nuevo estudiante de vinculación
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = EstudianteVinculacionService()
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Listar estudiantes de vinculación',
        description='Obtiene una lista de todos los estudiantes de vinculación activos.',
        parameters=[
            OpenApiParameter(
                name='solo_activos',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Si es true, solo devuelve estudiantes activos',
                default=True
            ),
        ],
        responses={
            200: ServiceResultListSerializer,
            500: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "status": "success",
                    "message": "Se encontraron 3 estudiantes",
                    "data": [
                        {
                            "id": 1,
                            "nombre": "Juan",
                            "apellido": "Pérez",
                            "email": "juan.perez@unl.edu.ec",
                            "dni": "1234567890",
                            "foto_perfil": None,
                            "rol": "ESTUDIANTE_VINCULACION",
                            "estado": True,
                            "fecha_registro": "2024-01-15",
                            "carrera": "Ingeniería en Sistemas",
                            "semestre": "7"
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    )
    def get(self, request):
        """Lista todos los estudiantes de vinculación"""
        solo_activos = request.query_params.get('solo_activos', 'true').lower() == 'true'
        result = self.service.listar_estudiantes(solo_activos=solo_activos)
        return self.service_response(result)
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Crear estudiante de vinculación',
        description='Crea una nueva cuenta de estudiante de vinculación. El correo debe ser institucional (@unl.edu.ec).',
        request=EstudianteVinculacionInputSerializer,
        responses={
            201: ServiceResultDetailSerializer,
            400: ServiceResultSerializer,
            409: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Ejemplo de creación',
                value={
                    "nombre": "Juan",
                    "apellido": "Pérez",
                    "email": "juan.perez@unl.edu.ec",
                    "dni": "1234567890",
                    "clave": "password123",
                    "carrera": "Ingeniería en Sistemas",
                    "semestre": "7"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "status": "success",
                    "message": "Estudiante de vinculación creado exitosamente",
                    "data": {
                        "id": 1,
                        "nombre": "Juan",
                        "apellido": "Pérez",
                        "email": "juan.perez@unl.edu.ec",
                        "dni": "1234567890",
                        "foto_perfil": None,
                        "rol": "ESTUDIANTE_VINCULACION",
                        "estado": True,
                        "fecha_registro": "2024-01-15",
                        "carrera": "Ingeniería en Sistemas",
                        "semestre": "7"
                    }
                },
                response_only=True,
            ),
            OpenApiExample(
                'Error de validación - Email no institucional',
                value={
                    "status": "validation_error",
                    "message": "Error de validación",
                    "errors": ["El correo debe ser institucional (@unl.edu.ec)"]
                },
                response_only=True,
            ),
        ]
    )
    def post(self, request):
        """Crea un nuevo estudiante de vinculación"""
        result = self.service.crear_estudiante(request.data)
        return self.service_response(result, created=True)


class EstudianteVinculacionDetailController(BaseController):
    """
    Controlador para operaciones sobre un estudiante específico.
    
    GET: Obtiene los detalles de un estudiante
    PUT: Actualiza un estudiante
    DELETE: Da de baja un estudiante (soft delete)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = EstudianteVinculacionService()
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Obtener estudiante de vinculación',
        description='Obtiene los detalles de un estudiante de vinculación por su ID.',
        responses={
            200: ServiceResultDetailSerializer,
            404: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "status": "success",
                    "message": "Estudiante encontrado",
                    "data": {
                        "id": 1,
                        "nombre": "Juan",
                        "apellido": "Pérez",
                        "email": "juan.perez@unl.edu.ec",
                        "dni": "1234567890",
                        "foto_perfil": None,
                        "rol": "ESTUDIANTE_VINCULACION",
                        "estado": True,
                        "fecha_registro": "2024-01-15",
                        "carrera": "Ingeniería en Sistemas",
                        "semestre": "7"
                    }
                },
                response_only=True,
            ),
        ]
    )
    def get(self, request, pk):
        """Obtiene un estudiante por ID"""
        result = self.service.obtener_estudiante(pk)
        return self.service_response(result)
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Actualizar estudiante de vinculación',
        description='Actualiza los datos de un estudiante de vinculación existente.',
        request=EstudianteVinculacionUpdateSerializer,
        responses={
            200: ServiceResultDetailSerializer,
            400: ServiceResultSerializer,
            404: ServiceResultSerializer,
            409: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Ejemplo de actualización',
                value={
                    "nombre": "Juan Carlos",
                    "semestre": "8"
                },
                request_only=True,
            ),
        ]
    )
    def put(self, request, pk):
        """Actualiza un estudiante"""
        result = self.service.actualizar_estudiante(pk, request.data)
        return self.service_response(result)
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Dar de baja estudiante de vinculación',
        description='Da de baja (desactiva) un estudiante de vinculación. Es un soft delete, el estudiante no se elimina permanentemente.',
        responses={
            200: ServiceResultSerializer,
            404: ServiceResultSerializer,
            400: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "status": "success",
                    "message": "Estudiante dado de baja exitosamente",
                    "data": {"id": 1, "estado": False}
                },
                response_only=True,
            ),
        ]
    )
    def delete(self, request, pk):
        """Da de baja un estudiante (soft delete)"""
        result = self.service.dar_de_baja(pk)
        return self.service_response(result)


class EstudianteVinculacionReactivarController(BaseController):
    """
    Controlador para reactivar estudiantes dados de baja.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = EstudianteVinculacionService()
    
    @extend_schema(
        tags=['Estudiantes de Vinculación'],
        summary='Reactivar estudiante de vinculación',
        description='Reactiva un estudiante de vinculación que fue dado de baja.',
        responses={
            200: ServiceResultDetailSerializer,
            404: ServiceResultSerializer,
            400: ServiceResultSerializer,
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "status": "success",
                    "message": "Estudiante reactivado exitosamente",
                    "data": {
                        "id": 1,
                        "nombre": "Juan",
                        "apellido": "Pérez",
                        "estado": True
                    }
                },
                response_only=True,
            ),
        ]
    )
    def post(self, request, pk):
        """Reactiva un estudiante dado de baja"""
        result = self.service.reactivar_estudiante(pk)
        return self.service_response(result)



