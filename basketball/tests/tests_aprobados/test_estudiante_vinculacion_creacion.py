"""
Tests completos para la creación de Estudiantes de Vinculación usando mocks.

Estos tests mockean el service directamente para evitar acceso a BD.
"""

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings

from basketball.controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)


class TestEstudianteVinculacionCreacion(SimpleTestCase):
    """Tests para la creación de estudiantes de vinculación."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.factory = APIRequestFactory()
        self.view = EstudianteVinculacionController.as_view({"post": "create"})

        payload = {"role": "ADMIN", "sub": "admin-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    # =========================================================================
    # Tests de creación exitosa
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_completo_exitoso(self, mock_get_token):
        """Test: Crear un estudiante de vinculación con todos los datos válidos."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            # Configurar mock para retornar resultado exitoso
            mock_service.create_estudiante.return_value = {
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
                    "email": "juan@unl.edu.ec",
                },
            }

            data = {
                "persona": {
                    "identification": "1103456784",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan@unl.edu.ec",
                    "password": "Pass123!",
                },
                "estudiante": {
                    "carrera": "Ingeniería en Sistemas",
                    "semestre": "5",
                },
            }

            request = self.factory.post(
                "/api/estudiantes-vinculacion/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(response.data["msg"], "Estudiante creado correctamente")
            self.assertIn("estudiante", response.data["data"])
            mock_service.create_estudiante.assert_called_once()

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_con_semestre_letra_exitoso(self, mock_get_token):
        """Test: Crear un estudiante con semestre en formato letra (A-J)."""
        mock_get_token.return_value = "admin-token-123"

        with patch.object(EstudianteVinculacionController, "service") as mock_service:
            mock_service.create_estudiante.return_value = {
                "estudiante": {
                    "id": 2,
                    "persona_external": "persona-002",
                    "carrera": "Ingeniería Civil",
                    "semestre": "A",
                    "eliminado": False,
                },
                "persona": {
                    "external": "persona-002",
                    "identification": "0912345675",
                    "first_name": "María",
                    "last_name": "González",
                    "email": "maria@unl.edu.ec",
                },
            }

            data = {
                "persona": {
                    "identification": "0912345675",
                    "first_name": "María",
                    "last_name": "González",
                    "email": "maria@unl.edu.ec",
                    "password": "Pass123!",
                },
                "estudiante": {
                    "carrera": "Ingeniería Civil",
                    "semestre": "A",
                },
            }

            request = self.factory.post(
                "/api/estudiantes-vinculacion/",
                data=data,
                format="json",
                HTTP_AUTHORIZATION=self.auth_header,
            )
            response = self.view(request)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["status"], "success")

    # =========================================================================
    # Tests de validación de semestre
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_con_semestre_invalido_falla(self, mock_get_token):
        """Test: Falla cuando se proporciona un semestre inválido."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "persona": {
                "identification": "1712345675",
                "first_name": "Pedro",
                "last_name": "López",
                "email": "pedro@unl.edu.ec",
                "password": "Pass123!",
            },
            "estudiante": {
                "carrera": "Ingeniería Mecánica",
                "semestre": "15",  # Inválido: debe ser 1-10 o A-J
            },
        }

        request = self.factory.post(
            "/api/estudiantes-vinculacion/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Error de validación")
        self.assertIn("estudiante", response.data["data"])

    # =========================================================================
    # Tests de validación de carrera
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_con_carrera_corta_falla(self, mock_get_token):
        """Test: Falla cuando el nombre de la carrera es muy corto."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "persona": {
                "identification": "0101234565",
                "first_name": "Ana",
                "last_name": "Martínez",
                "email": "ana@unl.edu.ec",
                "password": "Pass123!",
            },
            "estudiante": {
                "carrera": "Ing",  # Muy corto: mínimo 5 caracteres
                "semestre": "3",
            },
        }

        request = self.factory.post(
            "/api/estudiantes-vinculacion/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Error de validación")

    # =========================================================================
    # Tests de validación de persona
    # =========================================================================

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_sin_persona_falla(self, mock_get_token):
        """Test: Falla cuando no se proporcionan datos de persona."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "estudiante": {
                "carrera": "Ingeniería Industrial",
                "semestre": "2",
            },
        }

        request = self.factory.post(
            "/api/estudiantes-vinculacion/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    @patch(
        "basketball.controllers.estudiante_vinculacion_controller.get_user_module_token"
    )
    def test_crear_estudiante_sin_datos_estudiante_falla(self, mock_get_token):
        """Test: Falla cuando no se proporcionan datos del estudiante."""
        mock_get_token.return_value = "admin-token-123"

        data = {
            "persona": {
                "identification": "1343210983",
                "first_name": "Carlos",
                "last_name": "Rodríguez",
                "email": "carlos@unl.edu.ec",
                "password": "Pass123!",
            },
        }

        request = self.factory.post(
            "/api/estudiantes-vinculacion/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_crear_estudiante_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        data = {
            "persona": {
                "identification": "0702345679",
                "first_name": "Luis",
                "last_name": "Hernández",
                "email": "luis@unl.edu.ec",
                "password": "Pass123!",
            },
            "estudiante": {
                "carrera": "Ingeniería de Sistemas",
                "semestre": "4",
            },
        }

        request = self.factory.post(
            "/api/estudiantes-vinculacion/",
            data=data,
            format="json",
        )
        response = self.view(request)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
