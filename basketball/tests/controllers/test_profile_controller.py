"""Pruebas unitarias para ProfileController."""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status

from basketball.controllers.profile_controller import ProfileController
from basketball.authentication import AuthenticatedUser


class TestProfileController(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.controller = ProfileController()
        self.controller.service = MagicMock()

        # Mock user
        self.user = AuthenticatedUser(pk="ext-123", role="ADMIN", payload={})
        self.user.email = "admin@test.com"
        self.user.name = "Admin User"

    @patch("basketball.controllers.profile_controller.get_user_module_token")
    def test_me_success(self, mock_get_token):
        """Test que el endpoint me retorna datos correctamente."""
        mock_get_token.return_value = "fake-token"

        expected_data = {
            "role": "ADMIN",
            "email": "admin@test.com",
            "name": "Admin User",
            "data": {"some": "data"},
        }
        self.controller.service.get_profile_data.return_value = expected_data

        request = self.factory.get("/api/profile/me/")
        request.user = self.user
        request.auth = "local-token"

        response = self.controller.me(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente con 'data' que contiene los datos del perfil
        actual_data = response.data.get("data", response.data)
        self.assertEqual(actual_data, expected_data)
        self.controller.service.get_profile_data.assert_called_with(
            self.user, "fake-token"
        )

    @patch("basketball.controllers.profile_controller.get_user_module_token")
    def test_me_no_token(self, mock_get_token):
        """Test que falla si no hay token del módulo de usuarios."""
        mock_get_token.return_value = None

        request = self.factory.get("/api/profile/me/")
        request.user = self.user
        request.auth = "local-token"

        response = self.controller.me(request)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
