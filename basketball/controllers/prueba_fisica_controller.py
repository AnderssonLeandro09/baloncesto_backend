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

# Constantes para mensajes de error
MSG_ERROR_INTERNO = "Error interno del servidor"
MSG_ID_INVALIDO = "ID inválido"
MSG_PRUEBA_NO_ENCONTRADA = "Prueba física no encontrada"
MSG_DATOS_INVALIDOS = "Datos de entrada inválidos"


def _build_error_response(msg, code=500, data=None):
    """Construye una respuesta de error estándar."""
    return {
        "msg": msg,
        "data": data,
        "code": code,
        "status": "error",
    }


def _build_success_response(msg, data, code=200):
    """Construye una respuesta exitosa estándar."""
    return {
        "msg": msg,
        "data": data,
        "code": code,
        "status": "success",
    }


def _validate_pk(pk):
    """Valida que pk sea un entero válido. Retorna (pk_int, error_response)."""
    try:
        return int(pk), None
    except (TypeError, ValueError):
        return None, Response(
            _build_error_response(MSG_ID_INVALIDO, 400),
            status=status.HTTP_400_BAD_REQUEST,
        )


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
                _build_success_response(
                    "Listado de pruebas físicas obtenido exitosamente", pruebas
                ),
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en list pruebas físicas", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
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
                _build_success_response(
                    "Lista de atletas habilitados obtenida exitosamente", atletas
                ),
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en atletas_habilitados", exc_info=True)
            return Response(
                _build_error_response("Error al obtener atletas habilitados"),
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
                _build_error_response(MSG_DATOS_INVALIDOS, 400, serializer.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.create_prueba_fisica(
                serializer.validated_data, user=request.user
            )
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                _build_success_response(
                    "Prueba física creada exitosamente", prueba_completa, 201
                ),
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as exc:
            return Response(
                _build_error_response(str(exc), 400),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                _build_error_response(str(exc), 403),
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en create prueba física", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer})
    def retrieve(self, request, pk=None):
        """Obtiene una prueba física por ID."""
        token = get_user_module_token()

        pk, error_response = _validate_pk(pk)
        if error_response:
            return error_response

        try:
            prueba = self.service.get_prueba_fisica_completa(
                pk, token, user=request.user
            )
            if not prueba:
                return Response(
                    _build_error_response(MSG_PRUEBA_NO_ENCONTRADA, 404),
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _build_success_response("Prueba física obtenida exitosamente", prueba),
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                _build_error_response(str(exc), 400),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.error("Error en retrieve prueba física", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        request=PruebaFisicaInputSerializer,
        responses={200: PruebaFisicaResponseSerializer},
    )
    def update(self, request, pk=None):
        """Actualiza una prueba física existente."""
        token = get_user_module_token()

        pk, error_response = _validate_pk(pk)
        if error_response:
            return error_response

        serializer = PruebaFisicaInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                _build_error_response(MSG_DATOS_INVALIDOS, 400, serializer.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            prueba = self.service.update_prueba_fisica(
                pk, serializer.validated_data, user=request.user
            )
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                _build_success_response(
                    "Prueba física actualizada exitosamente", prueba_completa
                ),
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                _build_error_response(str(exc), 400),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                _build_error_response(str(exc), 403),
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en update prueba física", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(responses={200: PruebaFisicaResponseSerializer})
    @action(detail=True, methods=["patch"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        """Cambia el estado de la prueba física."""
        token = get_user_module_token()

        pk, error_response = _validate_pk(pk)
        if error_response:
            return error_response

        try:
            prueba = self.service.toggle_estado(pk, user=request.user)
            prueba_completa = self.service.get_prueba_fisica_completa(
                prueba.id, token, user=request.user
            )
            return Response(
                _build_success_response(
                    "Estado de la prueba física actualizado exitosamente",
                    prueba_completa,
                ),
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                _build_error_response(str(exc), 400),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied as exc:
            return Response(
                _build_error_response(str(exc), 403),
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logger.error("Error en toggle_estado prueba física", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
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
                _build_success_response(
                    "Pruebas físicas del atleta obtenidas exitosamente", pruebas
                ),
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Error en by_atleta pruebas físicas", exc_info=True)
            return Response(
                _build_error_response(MSG_ERROR_INTERNO),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
