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
            pruebas = self.service.get_all_pruebas_fisicas_completas(
                token, user=request.user
            )
            return Response(
                {
                    "msg": "Listado de pruebas físicas obtenido exitosamente",
                    "data": pruebas,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en list pruebas físicas", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        responses={200: serializers.ListField(child=serializers.DictField())}
    )
    @action(detail=False, methods=["get"], url_path="atletas-habilitados")
    def atletas_habilitados(self, request):
        """Obtiene la lista de atletas con inscripción habilitada."""
        token = get_user_module_token()
        try:
            atletas = self.service.get_atletas_habilitados_con_persona(
                token, user=request.user
            )
            return Response(
                {
                    "msg": "Lista de atletas habilitados obtenida exitosamente",
                    "data": atletas,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en atletas_habilitados", exc_info=True)
            return Response(
                {
                    "msg": "Error al obtener atletas habilitados",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
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
            return Response(
                {
                    "msg": "Datos de entrada inválidos",
                    "data": serializer.errors,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.create_prueba_fisica(
                serializer.validated_data, user=request.user
            )
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                {
                    "msg": "Prueba física creada exitosamente",
                    "data": prueba_completa,
                    "code": 201,
                    "status": "success",
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 403,
                    "status": "error",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en create prueba física", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
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
                {
                    "msg": "ID inválido",
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.get_prueba_fisica_completa(
                pk, token, user=request.user
            )
            if not prueba:
                return Response(
                    {
                        "msg": "Prueba física no encontrada",
                        "data": None,
                        "code": 404,
                        "status": "error",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {
                    "msg": "Prueba física obtenida exitosamente",
                    "data": prueba,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.error("Error en retrieve prueba física", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
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
                {
                    "msg": "ID inválido",
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PruebaFisicaInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {
                    "msg": "Datos de entrada inválidos",
                    "data": serializer.errors,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.update_prueba_fisica(
                pk, serializer.validated_data, user=request.user
            )
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                {
                    "msg": "Prueba física actualizada exitosamente",
                    "data": prueba_completa,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 403,
                    "status": "error",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en update prueba física", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
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
                {
                    "msg": "ID inválido",
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.toggle_estado(pk, user=request.user)
            # Obtener datos completos para la respuesta
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                {
                    "msg": "Estado de la prueba física actualizado exitosamente",
                    "data": prueba_completa,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 400,
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                {
                    "msg": str(exc),
                    "data": None,
                    "code": 403,
                    "status": "error",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en toggle_estado prueba física", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="atleta/(?P<atleta_id>[^/.]+)")
    def by_atleta(self, request, atleta_id=None):
        """Obtiene todas las pruebas físicas de un atleta específico."""
        token = get_user_module_token()
        try:
            pruebas = self.service.get_pruebas_by_atleta_completas(
                atleta_id, token, user=request.user
            )
            return Response(
                {
                    "msg": "Pruebas físicas del atleta obtenidas exitosamente",
                    "data": pruebas,
                    "code": 200,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en by_atleta pruebas físicas", exc_info=True)
            return Response(
                {
                    "msg": "Error interno del servidor",
                    "data": None,
                    "code": 500,
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
