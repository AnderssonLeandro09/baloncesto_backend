"""Tests del controlador de Autenticación."""

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIRequestFactory
from basketball.controllers.auth_controller import AuthController


class AuthControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = AuthController.as_view({"post": "login"})

    @patch("basketball.controllers.auth_controller.requests.post")
    def test_login_success(self, mock_post):
        # Mock response from external user service
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "external": "ext-123",
                "email": "test@test.com",
                "name": "Test User",
            }
        }
        mock_post.return_value = mock_response

        # Mock database lookups for roles
        with patch(
            "basketball.controllers.auth_controller.Administrador.objects.filter"
        ) as mock_admin, patch(
            "basketball.controllers.auth_controller.Entrenador.objects.filter"
        ) as mock_entrenador, patch(
            "basketball.controllers.auth_controller.EstudianteVinculacion.objects.filter"
        ) as mock_estudiante:
            mock_admin.return_value.exists.return_value = True

            payload = {"email": "test@test.com", "password": "password123"}
            request = self.factory.post("/api/auth/login/", payload, format="json")
            response = self.view(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("token", response.data)
            self.assertEqual(response.data["user"]["role"], "ADMIN")

    @patch("basketball.controllers.auth_controller.requests.post")
    def test_login_invalid_credentials(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        payload = {"email": "test@test.com", "password": "wrong"}
        request = self.factory.post("/api/auth/login/", payload, format="json")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("basketball.controllers.auth_controller.requests.post")
    def test_login_service_unavailable(self, mock_post):
        from requests import RequestException

        mock_post.side_effect = RequestException("Connection error")

        payload = {"email": "test@test.com", "password": "password123"}
        request = self.factory.post("/api/auth/login/", payload, format="json")
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
