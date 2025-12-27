"""
Controlador base para el módulo Basketball

Implementación de BaseController y utilidades para API REST
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from basketball.services.base_service import ServiceResult, ResultStatus


class BaseController(APIView):
    """
    Controlador base que proporciona métodos comunes para todos los controladores.
    """

    service = None

    def get_status_code(self, result: ServiceResult) -> int:
        """
        Obtiene el código de estado HTTP basado en el resultado del servicio.

        Args:
            result: Resultado del servicio

        Returns:
            int: Código de estado HTTP
        """
        status_map = {
            ResultStatus.SUCCESS: status.HTTP_200_OK,
            ResultStatus.ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ResultStatus.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
            ResultStatus.NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ResultStatus.CONFLICT: status.HTTP_409_CONFLICT,
        }
        return status_map.get(result.status, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def service_response(
        self, result: ServiceResult, created: bool = False
    ) -> Response:
        """
        Genera una Response de DRF basada en el resultado del servicio.

        Args:
            result: Resultado del servicio
            created: Si True y es exitoso, devuelve 201 CREATED

        Returns:
            Response: Respuesta HTTP
        """
        status_code = self.get_status_code(result)

        if created and result.is_success:
            status_code = status.HTTP_201_CREATED

        return Response(result.to_dict(), status=status_code)
