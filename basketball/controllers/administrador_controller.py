"""Controlador para Administrador."""

from rest_framework import status, viewsets
from rest_framework.response import Response
from ..services.administrador_service import AdministradorService
from ..serializers import AdministradorSerializer
from ..permissions import IsAdmin


class AdministradorController(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    serializer_class = AdministradorSerializer
    service = AdministradorService()

    def list(self, request):
        token = request.headers.get('Authorization')
        try:
            data = self.service.get_all_administradores(token)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        token = request.headers.get('Authorization')
        payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
        persona_data = payload.get('persona') or payload.get('persona_data')
        administrador_data = payload.get('administrador') or payload.get('administrador_data') or {}
        try:
            result = self.service.create_administrador(persona_data or {}, administrador_data, token)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        token = request.headers.get('Authorization')
        try:
            data = self.service.get_administrador_by_id(pk, token)
            if not data:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        token = request.headers.get('Authorization')
        payload = request.data.dict() if hasattr(request.data, 'dict') else request.data
        persona_data = payload.get('persona') or payload.get('persona_data')
        administrador_data = payload.get('administrador') or payload.get('administrador_data') or {}
        try:
            result = self.service.update_administrador(pk, persona_data or {}, administrador_data, token)
            if not result:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        success = self.service.delete_administrador(pk)
        if not success:
            return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
