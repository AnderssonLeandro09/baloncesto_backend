"""
Tests completos para actualización de Estudiantes de Vinculación usando mocks.

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


class TestEstudianteVinculacionUpdate(SimpleTestCase):
    """Tests para actualización de estudiantes de vinculación."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.factory = APIRequestFactory()
        self.view = EstudianteVinculacionController.as_view({"put": "update"})

        payload = {"role": "ADMIN", "sub": "admin-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    # =========================================================================
    # Tests de actualización exitosa
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_completo_exitoso(self, mock_get_token):
        """Test: Actualizar todos los datos de un estudiante."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.update_estudiante.return_value = {
                "estudiante": {
                    "id": 1,
                    "persona_external": "persona-001",
                    "carrera": "Ingeniería Civil",
                    "semestre": "6",
                    "eliminado": False,
                },
                "persona": {
                    "external": "persona-001",
                    "identification": "1103456784",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan.updated@unl.edu.ec",
                },
            }

            data = {
                "persona": {
                    "identification": "1103456784",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan.updated@unl.edu.ec",
                },
                "estudiante": {
                    "carrera": "Ingeniería Civil",
                    "semestre": "6",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/1/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(
                response.data["msg"], "Estudiante actualizado correctamente"
            )
            self.assertIn("estudiante", response.data["data"])
            mock_service.update_estudiante.assert_called_once()

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_solo_datos_estudiante_exitoso(self, mock_get_token):
        """Test: Actualizar solo los datos del estudiante."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.update_estudiante.return_value = {
                "estudiante": {
                    "id": 1,
                    "persona_external": "persona-001",
                    "carrera": "Ingeniería Industrial",
                    "semestre": "7",
                    "eliminado": False,
                },
                "persona": {"external": "persona-001", "identification": "1103456784"},
            }

            data = {
                "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
                "estudiante": {
                    "carrera": "Ingeniería Industrial",
                    "semestre": "7",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/1/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_solo_datos_persona_exitoso(self, mock_get_token):
        """Test: Actualizar solo los datos de la persona."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.update_estudiante.return_value = {
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
                    "first_name": "Juan Actualizado",
                    "email": "juan.new@unl.edu.ec",
                },
            }

            data = {
                "persona": {
                    "identification": "1103456784",
                    "first_name": "Juan Actualizado",
                    "email": "juan.new@unl.edu.ec",
                },
                "estudiante": {
                    "carrera": "Ingeniería en Sistemas",
                    "semestre": "5",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/1/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")

    # =========================================================================
    # Tests de errores
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_inexistente(self, mock_get_token):
        """Test: Intentar actualizar un estudiante que no existe."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.update_estudiante.return_value = None

            data = {
                "persona": {
                    "identification": "1103456784",
                    "first_name": "Juan",
                    "email": "juan@unl.edu.ec",
                },
                "estudiante": {
                    "carrera": "Ingeniería Civil",
                    "semestre": "6",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/999/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=999)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["msg"], "Estudiante no encontrado")

    # =========================================================================
    # Tests de validación
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_semestre_invalido(self, mock_get_token):
        """Test: Falla cuando se proporciona un semestre inválido."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
            "estudiante": {
                "carrera": "Ingeniería en Sistemas",
                "semestre": "15",  # Inválido
            },
        }

        request = self.factory.put(
            "/api/estudiantes-vinculacion/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertIn("estudiante", response.data["data"])

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_carrera_corta(self, mock_get_token):
        """Test: Falla cuando la carrera es muy corta."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
            "estudiante": {
                "carrera": "Ing",  # Muy corto
                "semestre": "5",
            },
        }

        request = self.factory.put(
            "/api/estudiantes-vinculacion/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_eliminado(self, mock_get_token):
        """Test: No se puede actualizar un estudiante eliminado."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            # El servicio retorna None para estudiantes eliminados
            mock_service.update_estudiante.return_value = None

            data = {
                "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
                "estudiante": {
                    "carrera": "Ingeniería Civil",
                    "semestre": "6",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/1/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_actualizar_estudiante_con_id_negativo(self, mock_get_token):
        """Test: No se puede actualizar con ID negativo."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.update_estudiante.return_value = None

            data = {
                "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
                "estudiante": {
                    "carrera": "Ingeniería Civil",
                    "semestre": "6",
                },
            }

            request = self.factory.put(
                "/api/estudiantes-vinculacion/-1/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request, pk=-1)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_actualizar_estudiante_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        data = {
            "persona": {"identification": "1103456784", "email": "juan@unl.edu.ec"},
            "estudiante": {
                "carrera": "Ingeniería Civil",
                "semestre": "6",
            },
        }

        request = self.factory.put(
            "/api/estudiantes-vinculacion/1/",
            data=data,
            format="json",
        )
        response = self.view(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
