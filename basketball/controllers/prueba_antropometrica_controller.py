"""
Controlador para PruebaAntropometrica
"""

import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from ..services.model_services import PruebaAntropometricaService
from ..serializar.prueba_antropometrica import (
    PruebaAntropometricaCreateDTO,
    PruebaAntropometricaResponseDTO,
    PruebaAntropometricaGraficaDTO,
)
from ..permissions import BaseRolePermission

logger = logging.getLogger(__name__)


class PruebaAntropometricaPermission(BaseRolePermission):
    """Permiso para registrar pruebas antropométricas"""

    allowed_roles = ["ENTRENADOR", "ESTUDIANTE_VINCULACION"]


class PruebaAntropometricaController(viewsets.ViewSet):
    """
    Controlador para operaciones CRUD de Pruebas Antropométricas
    """

    permission_classes = [PruebaAntropometricaPermission]
    service = PruebaAntropometricaService()

    @extend_schema(
        request=PruebaAntropometricaCreateDTO,
        responses={201: PruebaAntropometricaResponseDTO},
    )
    def create(self, request):
        """
        Crea una nueva prueba antropométrica
        """
        serializer = PruebaAntropometricaCreateDTO(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            prueba = self.service.crear_prueba(serializer.validated_data, request.user)
            response_serializer = PruebaAntropometricaResponseDTO(prueba)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error al crear prueba antropométrica: {e}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseDTO(many=True)})
    def list(self, request):
        """
        Lista todas las pruebas activas
        """
        try:
            pruebas = self.service.obtener_todas_activas()
            serializer = PruebaAntropometricaResponseDTO(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al listar pruebas: {e}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseDTO})
    def retrieve(self, request, pk=None):
        """
        Obtiene una prueba por ID
        """
        try:
            prueba = self.service.obtener_por_id(int(pk))
            if not prueba:
                return Response(
                    {"error": "Prueba no encontrada"}, status=status.HTTP_404_NOT_FOUND
                )
            serializer = PruebaAntropometricaResponseDTO(prueba)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"error": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al obtener prueba {pk}: {e}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaResponseDTO(many=True)})
    @action(detail=False, methods=["get"], url_path=r"atleta/(?P<atleta_id>\d+)")
    def por_atleta(self, request, atleta_id=None):
        """
        Obtiene todas las pruebas de un atleta
        """
        try:
            pruebas = self.service.obtener_por_atleta(int(atleta_id))
            serializer = PruebaAntropometricaResponseDTO(pruebas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"error": "ID de atleta inválido"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al obtener pruebas del atleta {atleta_id}: {e}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaAntropometricaGraficaDTO(many=True)})
    @action(detail=False, methods=["get"], url_path=r"grafica/(?P<atleta_id>\d+)")
    def grafica(self, request, atleta_id=None):
        """
        Obtiene datos para gráficas de un atleta
        """
        try:
            datos = self.service.obtener_datos_grafica(int(atleta_id))
            serializer = PruebaAntropometricaGraficaDTO(datos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"error": "ID de atleta inválido"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"Error al obtener datos de gráfica para atleta {atleta_id}: {e}"
            )
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: dict})
    @action(detail=True, methods=["patch"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        """
        Desactiva una prueba (no la elimina)
        """
        try:
            success = self.service.desactivar_prueba(int(pk), request.user)
            if success:
                return Response(
                    {"message": "Prueba desactivada correctamente"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Prueba no encontrada"}, status=status.HTTP_404_NOT_FOUND
                )
        except ValueError:
            return Response(
                {"error": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error al desactivar prueba {pk}: {e}")
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
