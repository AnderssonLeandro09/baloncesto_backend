"""
Tests completos para la baja lógica de Estudiantes de Vinculación usando mocks.

Estos tests usan el service real para validar todas las reglas de negocio,
solo se mockean las dependencias externas (DAO).
"""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings

from basketball.controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)
from basketball.models import EstudianteVinculacion


class TestEstudianteVinculacionBaja(SimpleTestCase):
    """Tests para la baja lógica de estudiantes de vinculación."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = EstudianteVinculacionController.as_view({"delete": "destroy"})

        payload = {"role": "ADMIN", "sub": "admin-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de baja exitosa
    # =========================================================================

    def test_dar_baja_estudiante_exitoso(self):
        """Test: Dar de baja un estudiante existente."""
        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.delete_estudiante.return_value = True

            request = self.factory.delete(
                "/api/estudiantes-vinculacion/1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(response.data["msg"], "Estudiante eliminado correctamente")
            mock_service.delete_estudiante.assert_called_once_with(1)

    # =========================================================================
    # Tests de error: estudiante no existe
    # =========================================================================

    def test_dar_baja_estudiante_inexistente_retorna_404(self):
        """Test: Intentar dar de baja un estudiante que no existe."""
        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.delete_estudiante.return_value = False

            request = self.factory.delete(
                "/api/estudiantes-vinculacion/999/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=999)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["msg"], "Estudiante no encontrado")

    def test_dar_baja_estudiante_ya_eliminado_retorna_404(self):
        """Test: Intentar dar de baja un estudiante ya eliminado."""
        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.delete_estudiante.return_value = False

            request = self.factory.delete(
                "/api/estudiantes-vinculacion/1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["msg"], "Estudiante no encontrado")

    # =========================================================================
    # Tests de validación de ID
    # =========================================================================

    def test_dar_baja_con_id_negativo_retorna_404(self):
        """Test: Intentar dar de baja con ID negativo."""
        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.delete_estudiante.return_value = False

            request = self.factory.delete(
                "/api/estudiantes-vinculacion/-1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=-1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    def test_dar_baja_con_id_cero_retorna_404(self):
        """Test: Intentar dar de baja con ID cero."""
        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.delete_estudiante.return_value = False

            request = self.factory.delete(
                "/api/estudiantes-vinculacion/0/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=0)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_dar_baja_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        request = self.factory.delete("/api/estudiantes-vinculacion/1/")
        response = self.view(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
