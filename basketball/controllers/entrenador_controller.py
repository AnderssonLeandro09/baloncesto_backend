"""
Controlador para Entrenador

TODO: Implementar controlador
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from basketball.controllers.base_controller import BaseController
from basketball.services.entrenador_service import EntrenadorService
from basketball.services.base_service import ResultStatus


class EntrenadorInputSerializer(serializers.Serializer):
	nombre = serializers.CharField(max_length=100)
	apellido = serializers.CharField(max_length=100)
	email = serializers.EmailField()
	dni = serializers.CharField(max_length=10)
	clave = serializers.CharField(max_length=255)
	especialidad = serializers.CharField(max_length=100)
	club_asignado = serializers.CharField(max_length=100)
	foto_perfil = serializers.CharField(max_length=255, required=False, allow_null=True)


class EntrenadorUpdateSerializer(serializers.Serializer):
	nombre = serializers.CharField(max_length=100, required=False)
	apellido = serializers.CharField(max_length=100, required=False)
	email = serializers.EmailField(required=False)
	especialidad = serializers.CharField(max_length=100, required=False)
	club_asignado = serializers.CharField(max_length=100, required=False)
	foto_perfil = serializers.CharField(max_length=255, required=False, allow_null=True)


class EntrenadorOutputSerializer(serializers.Serializer):
	id = serializers.IntegerField()
	nombre = serializers.CharField()
	apellido = serializers.CharField()
	email = serializers.EmailField()
	dni = serializers.CharField()
	foto_perfil = serializers.CharField(allow_null=True)
	rol = serializers.CharField()
	estado = serializers.BooleanField()
	fecha_registro = serializers.CharField(allow_null=True)
	especialidad = serializers.CharField()
	club_asignado = serializers.CharField()


class ServiceResultSerializer(serializers.Serializer):
	status = serializers.CharField()
	message = serializers.CharField()
	data = serializers.JSONField(required=False)
	errors = serializers.ListField(child=serializers.CharField(), required=False)


class EntrenadorListController(BaseController):
	"""Lista y crea entrenadores."""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.service = EntrenadorService()

	@extend_schema(
		tags=['Entrenadores'],
		summary='Listar entrenadores',
		parameters=[
			OpenApiParameter(
				name='solo_activos',
				type=OpenApiTypes.BOOL,
				location=OpenApiParameter.QUERY,
				description='Si true, solo devuelve activos',
				default=True
			)
		],
		responses={200: ServiceResultSerializer}
	)
	def get(self, request):
		solo_activos = request.query_params.get('solo_activos', 'true').lower() in ('1', 'true', 'yes')
		result = self.service.listar_entrenadores(solo_activos=solo_activos)
		return Response(result.to_dict(), status=status.HTTP_200_OK)

	@extend_schema(
		tags=['Entrenadores'],
		summary='Crear entrenador',
		request=EntrenadorInputSerializer,
		responses={201: ServiceResultSerializer, 400: ServiceResultSerializer, 409: ServiceResultSerializer}
	)
	def post(self, request):
		serializer = EntrenadorInputSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(ServiceResult.validation_error("Error de validación", list(serializer.errors.values())).to_dict(), status=status.HTTP_400_BAD_REQUEST)

		result = self.service.crear_entrenador(serializer.validated_data)
		if result.is_success:
			return Response(result.to_dict(), status=status.HTTP_201_CREATED)
		if result.status == ResultStatus.VALIDATION_ERROR:
			return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		if result.status == ResultStatus.CONFLICT:
			return Response(result.to_dict(), status=status.HTTP_409_CONFLICT)
		return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EntrenadorDetailController(BaseController):
	"""Operaciones sobre un entrenador especifico."""

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.service = EntrenadorService()

	@extend_schema(tags=['Entrenadores'], responses={200: ServiceResultSerializer, 404: ServiceResultSerializer})
	def get(self, request, pk: int):
		result = self.service.obtener_entrenador(pk)
		if result.is_success:
			return Response(result.to_dict(), status=status.HTTP_200_OK)
		if result.status == ResultStatus.NOT_FOUND:
			return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
		return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@extend_schema(tags=['Entrenadores'], request=EntrenadorUpdateSerializer, responses={200: ServiceResultSerializer, 400: ServiceResultSerializer, 404: ServiceResultSerializer})
	def put(self, request, pk: int):
		serializer = EntrenadorUpdateSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(ServiceResult.validation_error("Error de validación", list(serializer.errors.values())).to_dict(), status=status.HTTP_400_BAD_REQUEST)

		result = self.service.actualizar_entrenador(pk, serializer.validated_data)
		if result.is_success:
			return Response(result.to_dict(), status=status.HTTP_200_OK)
		if result.status == ResultStatus.VALIDATION_ERROR:
			return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		if result.status == ResultStatus.NOT_FOUND:
			return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
		return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	@extend_schema(tags=['Entrenadores'], responses={200: ServiceResultSerializer, 404: ServiceResultSerializer})
	def delete(self, request, pk: int):
		result = self.service.dar_de_baja(pk)
		if result.is_success:
			return Response(result.to_dict(), status=status.HTTP_200_OK)
		if result.status == ResultStatus.NOT_FOUND:
			return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
		if result.status == ResultStatus.CONFLICT:
			return Response(result.to_dict(), status=status.HTTP_409_CONFLICT)
		return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EntrenadorReactivarController(BaseController):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.service = EntrenadorService()

	@extend_schema(tags=['Entrenadores'], responses={200: ServiceResultSerializer, 404: ServiceResultSerializer, 409: ServiceResultSerializer})
	def post(self, request, pk: int):
		result = self.service.reactivar_entrenador(pk)
		if result.is_success:
			return Response(result.to_dict(), status=status.HTTP_200_OK)
		if result.status == ResultStatus.NOT_FOUND:
			return Response(result.to_dict(), status=status.HTTP_404_NOT_FOUND)
		if result.status == ResultStatus.CONFLICT:
			return Response(result.to_dict(), status=status.HTTP_409_CONFLICT)
		return Response(result.to_dict(), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

