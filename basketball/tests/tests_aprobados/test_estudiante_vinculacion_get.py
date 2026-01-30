"""
Tests completos para consulta (GET) de Estudiantes de Vinculación usando mocks.

Estos tests mockean el service directamente para evitar acceso a BD.
"""

from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings

from basketball.controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)


class TestEstudianteVinculacionGet(SimpleTestCase):
    """Tests para consulta de estudiantes de vinculación."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.factory = APIRequestFactory()

        payload = {"role": "ADMIN", "sub": "admin-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    # =========================================================================
    # Tests de listado
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_listar_estudiantes_exitoso(self, mock_get_token):
        """Test: Listar todos los estudiantes de vinculación."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.list_estudiantes.return_value = [
                {
                    "estudiante": {
                        "id": 1,
                        "persona_external": "persona-001",
                        "carrera": "Ingeniería en Sistemas",
                        "semestre": "5",
                        "eliminado": False,
                    },
                    "persona": {
                        "external": "persona-001",
                        "identification": "1103456784",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                    },
                },
                {
                    "estudiante": {
                        "id": 2,
                        "persona_external": "persona-002",
                        "carrera": "Ingeniería Civil",
                        "semestre": "3",
                        "eliminado": False,
                    },
                    "persona": {
                        "external": "persona-002",
                        "identification": "0912345675",
                        "first_name": "María",
                        "last_name": "González",
                    },
                },
            ]

            view = EstudianteVinculacionController.as_view({"get": "list"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(len(response.data["data"]), 2)
            mock_service.list_estudiantes.assert_called_once()

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_listar_estudiantes_vacio(self, mock_get_token):
        """Test: Listar cuando no hay estudiantes."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.list_estudiantes.return_value = []

            view = EstudianteVinculacionController.as_view({"get": "list"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(len(response.data["data"]), 0)

    # =========================================================================
    # Tests de retrieve (obtener uno)
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_obtener_estudiante_exitoso(self, mock_get_token):
        """Test: Obtener un estudiante específico por ID."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.get_estudiante.return_value = {
                "estudiante": {
                    "id": 1,
                    "persona_external": "persona-001",
                    "carrera": "Ingeniería en Sistemas",
                    "semestre": "5",
                    "eliminado": False,
                },
                "persona": {
                    "external": "persona-001",
                    "identification": "1103456784",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                },
            }

            view = EstudianteVinculacionController.as_view({"get": "retrieve"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIn("estudiante", response.data["data"])
            mock_service.get_estudiante.assert_called_once_with(1, "admin-token-123")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_obtener_estudiante_inexistente(self, mock_get_token):
        """Test: Intentar obtener un estudiante que no existe."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.get_estudiante.return_value = None

            view = EstudianteVinculacionController.as_view({"get": "retrieve"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/999/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request, pk=999)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["msg"], "Estudiante no encontrado")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_obtener_estudiante_eliminado(self, mock_get_token):
        """Test: Intentar obtener un estudiante eliminado (servicio retorna None)."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            # El servicio retorna None para estudiantes eliminados
            mock_service.get_estudiante.return_value = None

            view = EstudianteVinculacionController.as_view({"get": "retrieve"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests de validación de ID
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_obtener_estudiante_con_id_negativo(self, mock_get_token):
        """Test: Intentar obtener un estudiante con ID negativo."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.get_estudiante.return_value = None

            view = EstudianteVinculacionController.as_view({"get": "retrieve"})
            request = self.factory.get(
                "/api/estudiantes-vinculacion/-1/",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = view(request, pk=-1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_listar_sin_token_falla(self):
        """Test: Falla al listar sin token de autenticación."""
        view = EstudianteVinculacionController.as_view({"get": "list"})
        request = self.factory.get("/api/estudiantes-vinculacion/")
        response = view(request)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_obtener_sin_token_falla(self):
        """Test: Falla al obtener un estudiante sin token."""
        view = EstudianteVinculacionController.as_view({"get": "retrieve"})
        request = self.factory.get("/api/estudiantes-vinculacion/1/")
        response = view(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
