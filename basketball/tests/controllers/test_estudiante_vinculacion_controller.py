"""Tests del controlador de EstudianteVinculacion usando mocks."""

import jwt
from django.conf import settings
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.estudiante_vinculacion_controller import (
    EstudianteVinculacionController,
)


@patch("basketball.controllers.estudiante_vinculacion_controller.get_user_module_token")
class EstudianteVinculacionControllerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EstudianteVinculacionController.as_view(
            {
                "get": "list",
                "post": "create",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        )
        payload = {"role": "ADMIN", "sub": "test_user"}
        self.token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        self.auth_header = f"Bearer {self.token}"

    def test_list_returns_data(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        mock_service = MagicMock()
        mock_service.list_estudiantes.return_value = [
            {"estudiante": {"id": 1}},
        ]
        self.view.cls.service = mock_service

        request = self.factory.get(
            "/estudiantes-vinculacion/",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": [...], ...}
        self.assertEqual(len(response.data.get("data", response.data)), 1)

    def test_create_success(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        mock_service = MagicMock()
        mock_service.create_estudiante.return_value = {"estudiante": {"id": 1}}
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/estudiantes-vinculacion/",
            {
                "persona": {
                    "identification": "1234567890",
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "test@unl.edu.ec",
                    "password": "password123",
                },
                "estudiante": {"carrera": "Ing. en Sistemas", "semestre": "1"},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": {...}, ...}
        self.assertIn("data", response.data)

    def test_create_handles_error(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        mock_service = MagicMock()
        mock_service.create_estudiante.side_effect = Exception("bad")
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/estudiantes-vinculacion/",
            {"persona": {}, "estudiante": {}},
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("msg", response.data)

    def test_retrieve_not_found(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        view = EstudianteVinculacionController.as_view({"get": "retrieve"})
        mock_service = MagicMock()
        mock_service.get_estudiante.return_value = None
        view.cls.service = mock_service

        request = self.factory.get(
            "/estudiantes-vinculacion/9/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=9)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_success(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        view = EstudianteVinculacionController.as_view({"put": "update"})
        mock_service = MagicMock()
        mock_service.update_estudiante.return_value = {
            "estudiante": {"id": 2, "semestre": "2"}
        }
        view.cls.service = mock_service

        request = self.factory.put(
            "/estudiantes-vinculacion/2/",
            {"persona": {"external": "x"}, "estudiante": {"semestre": "2"}},
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = view(request, pk=2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": {"estudiante": {...}}, ...}
        data = response.data.get("data", response.data)
        self.assertEqual(data["estudiante"]["semestre"], "2")

    def test_destroy_success(self, mock_get_token):
        mock_get_token.return_value = "fake_token"
        view = EstudianteVinculacionController.as_view({"delete": "destroy"})
        mock_service = MagicMock()
        mock_service.delete_estudiante.return_value = True
        view.cls.service = mock_service

        request = self.factory.delete(
            "/estudiantes-vinculacion/3/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=3)

        # El controlador devuelve 200 con mensaje de éxito, no 204
        self.assertEqual(response.status_code, status.HTTP_200_OK)
