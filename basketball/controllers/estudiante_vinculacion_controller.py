"""Controlador para Estudiante de Vinculación."""

from rest_framework import status, viewsets
from rest_framework.response import Response

from ..permissions import IsAdmin
from ..serializers import EstudianteVinculacionSerializer
from ..services.estudiante_vinculacion_service import EstudianteVinculacionService


class EstudianteVinculacionController(viewsets.ViewSet):
	"""CRUD para estudiantes de vinculación."""

	permission_classes = [IsAdmin]
	serializer_class = EstudianteVinculacionSerializer
	service = EstudianteVinculacionService()

	def list(self, request):
		token = request.headers.get('Authorization')
		try:
			data = self.service.list_estudiantes(token)
			return Response(data, status=status.HTTP_200_OK)
		except Exception as exc:
			return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

	def retrieve(self, request, pk=None):
		token = request.headers.get('Authorization')
		try:
			data = self.service.get_estudiante(pk, token)
			if not data:
				return Response({'error': 'Estudiante no encontrado'}, status=status.HTTP_404_NOT_FOUND)
			return Response(data, status=status.HTTP_200_OK)
		except Exception as exc:
			return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

	def create(self, request):
		token = request.headers.get('Authorization')
		payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
		persona_data = payload.get('persona') or payload.get('persona_data')
		estudiante_data = payload.get('estudiante') or payload.get('estudiante_data') or {}
		try:
			result = self.service.create_estudiante(persona_data or {}, estudiante_data, token)
			return Response(result, status=status.HTTP_201_CREATED)
		except Exception as exc:
			return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

	def update(self, request, pk=None):
		token = request.headers.get('Authorization')
		payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
		persona_data = payload.get('persona') or payload.get('persona_data')
		estudiante_data = payload.get('estudiante') or payload.get('estudiante_data') or {}
		try:
			result = self.service.update_estudiante(pk, persona_data or {}, estudiante_data, token)
			if not result:
				return Response({'error': 'Estudiante no encontrado'}, status=status.HTTP_404_NOT_FOUND)
			return Response(result, status=status.HTTP_200_OK)
		except Exception as exc:
			return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

	def partial_update(self, request, pk=None):
		return self.update(request, pk)

	def destroy(self, request, pk=None):
		success = self.service.delete_estudiante(pk)
		if not success:
			return Response({'error': 'Estudiante no encontrado'}, status=status.HTTP_404_NOT_FOUND)
		return Response(status=status.HTTP_204_NO_CONTENT)
