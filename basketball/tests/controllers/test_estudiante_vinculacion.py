"""
Pruebas unitarias para los controllers/endpoints de EstudianteVinculacion
"""

from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from basketball.services.estudiante_vinculacion_service import (  # noqa: F401
    EstudianteVinculacionService,
)
from basketball.services.base_service import ServiceResult


class EstudianteVinculacionAPITests(APITestCase):
    """Pruebas para los endpoints del API usando Mocks"""

    def setUp(self):
        self.base_url = "/api/basketball/estudiantes-vinculacion/"
        self.valid_data = {
            "nombre": "Ana",
            "apellido": "Martínez",
            "email": "ana.martinez@unl.edu.ec",
            "clave": "password123",
            "dni": "5555555555",
            "carrera": "Enfermería",
            "semestre": "4",
        }
        self.mock_estudiante_data = {
            "id": 1,
            "nombre": "Ana",
            "apellido": "Martínez",
            "email": "ana.martinez@unl.edu.ec",
            "dni": "5555555555",
            "carrera": "Enfermería",
            "semestre": "4",
            "estado": True,
            "foto_perfil": None,
        }

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch('basketball.permissions.IsAdmin.has_permission', return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    # fmt: on
    def test_listar_estudiantes_vacio(self, MockService, mock_permission, mock_token):
        """GET lista vacía de estudiantes"""
        mock_service = MockService.return_value
        mock_service.list_estudiantes.return_value = []

        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # fmt: off
    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch('basketball.permissions.IsAdmin.has_permission', return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    # fmt: on
    def test_create_estudiante_exitoso(self, MockService, mock_permission, mock_token):
        """POST crear estudiante válido"""
        mock_service = MockService.return_value
        mock_service.create_estudiante.return_value = self.mock_estudiante_data

        response = self.client.post(self.base_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nombre"], "Ana")

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_create_estudiante_email_invalido(self, MockService, mock_permission, mock_token):
        """POST crear estudiante con email no institucional"""
        mock_service = MockService.return_value
        from django.core.exceptions import ValidationError
        mock_service.create_estudiante.side_effect = ValidationError("El email debe ser institucional (@unl.edu.ec)")

        self.valid_data["email"] = "ana@gmail.com"
        response = self.client.post(self.base_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_create_estudiante_duplicado(self, MockService, mock_permission, mock_token):
        """POST crear estudiante con email duplicado"""
        mock_service = MockService.return_value
        from django.core.exceptions import ValidationError
        mock_service.create_estudiante.side_effect = ValidationError("Ya existe un usuario con este email")

        response = self.client.post(self.base_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_obtener_estudiante_existente(self, MockService, mock_permission, mock_token):
        """GET obtener estudiante por ID"""
        mock_service = MockService.return_value
        mock_service.get_estudiante.return_value = self.mock_estudiante_data

        response = self.client.get(f"{self.base_url}1/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], 1)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_obtener_estudiante_no_existente(self, MockService, mock_permission, mock_token):
        """GET estudiante no existente devuelve 404"""
        mock_service = MockService.return_value
        mock_service.get_estudiante.return_value = None

        response = self.client.get(f"{self.base_url}99999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_actualizar_estudiante_exitoso(self, MockService, mock_permission, mock_token):
        """PUT actualizar estudiante"""
        mock_service = MockService.return_value
        updated_data = self.mock_estudiante_data.copy()
        updated_data["nombre"] = "Ana María"
        mock_service.update_estudiante.return_value = updated_data

        response = self.client.put(
            f"{self.base_url}1/", {"nombre": "Ana María"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nombre"], "Ana María")

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_dar_de_baja_estudiante(self, MockService, mock_permission, mock_token):
        """DELETE dar de baja estudiante"""
        mock_service = MockService.return_value
        deleted_data = self.mock_estudiante_data.copy()
        deleted_data["estado"] = False
        mock_service.delete_estudiante.return_value = True

        response = self.client.delete(f"{self.base_url}1/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_listar_solo_activos(self, MockService, mock_permission, mock_token):
        """GET listar solo estudiantes activos"""
        mock_service = MockService.return_value
        mock_service.list_estudiantes.return_value = []

        response = self.client.get(self.base_url, {"solo_activos": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @patch('basketball.controllers.estudiante_vinculacion_controller.get_user_module_token', return_value='mock_token')
    @patch("basketball.permissions.IsAdmin.has_permission", return_value=True)
    @patch(
        "basketball.controllers.estudiante_vinculacion_controller."
        "EstudianteVinculacionService"
    )
    def test_listar_incluyendo_inactivos(self, MockService, mock_permission, mock_token):
        """GET listar incluyendo inactivos"""
        mock_service = MockService.return_value
        inactive_data = self.mock_estudiante_data.copy()
        inactive_data["estado"] = False
        mock_service.list_estudiantes.return_value = [inactive_data]

        response = self.client.get(self.base_url, {"solo_activos": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
