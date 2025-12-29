"""Tests del controlador de Entrenador usando mocks."""

import jwt
from django.conf import settings
from unittest.mock import MagicMock

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.entrenador_controller import EntrenadorController


class EntrenadorControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = EntrenadorController.as_view(
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

    def test_list_returns_data(self):
        mock_service = MagicMock()
        mock_service.list_entrenadores.return_value = [
            {"entrenador": {"id": 1}},
        ]
        self.view.cls.service = mock_service

        request = self.factory.get(
            "/entrenadores/",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_success(self):
        mock_service = MagicMock()
        mock_service.create_entrenador.return_value = {"entrenador": {"id": 1}}
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/entrenadores/",
            {
                "persona": {
                    "first_name": "A",
                    "email": "test@unl.edu.ec",
                    "password": "password123",
                },
                "entrenador": {"especialidad": "Táctica", "club_asignado": "Club A"},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("entrenador", response.data)

    def test_create_handles_error(self):
        mock_service = MagicMock()
        mock_service.create_entrenador.side_effect = Exception("bad")
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/entrenadores/",
            {"persona": {}, "entrenador": {}},
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_retrieve_not_found(self):
        view = EntrenadorController.as_view({"get": "retrieve"})
        mock_service = MagicMock()
        mock_service.get_entrenador.return_value = None
        view.cls.service = mock_service

        request = self.factory.get(
            "/entrenadores/9/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=9)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_success(self):
        view = EntrenadorController.as_view({"put": "update"})
        mock_service = MagicMock()
        mock_service.update_entrenador.return_value = {
            "entrenador": {"id": 2, "especialidad": "Físico"}
        }
        view.cls.service = mock_service

        request = self.factory.put(
            "/entrenadores/2/",
            {"persona": {"external": "x"}, "entrenador": {"especialidad": "Físico"}},
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = view(request, pk=2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["entrenador"]["especialidad"], "Físico")

    def test_destroy_success(self):
        view = EntrenadorController.as_view({"delete": "destroy"})
        mock_service = MagicMock()
        mock_service.delete_entrenador.return_value = True
        view.cls.service = mock_service

        request = self.factory.delete(
            "/entrenadores/3/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=3)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_forbidden_for_non_admin(self):
        # Create token with different role
        payload = {"role": "USER", "sub": "test_user"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        auth_header = f"Bearer {token}"

        request = self.factory.get(
            "/entrenadores/",
            HTTP_AUTHORIZATION=auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
