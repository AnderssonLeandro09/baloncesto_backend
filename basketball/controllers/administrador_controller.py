"""Controlador para Administrador."""

from rest_framework import status, viewsets
from rest_framework.response import Response
from ..services.administrador_service import AdministradorService
from ..serializers import AdministradorSerializer
from ..permissions import IsAdmin


class AdministradorController(viewsets.ViewSet):
    permission_classes = [IsAdmin]
    service = AdministradorService()

    def list(self, request):
        administradores = self.service.get_all_administradores()
        serializer = AdministradorSerializer(administradores, many=True)
        return Response(serializer.data)

    def create(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, 'dict') else request.data
            administrador = self.service.create_administrador(data)
            serializer = AdministradorSerializer(administrador)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        administrador = self.service.get_administrador_by_id(pk)
        if not administrador:
            return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdministradorSerializer(administrador)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            data = request.data.dict() if hasattr(request.data, 'dict') else request.data
            administrador = self.service.update_administrador(pk, data)
            if not administrador:
                return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            serializer = AdministradorSerializer(administrador)
            return Response(serializer.data)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        success = self.service.delete_administrador(pk)
        if not success:
            return Response({'error': 'Administrador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
