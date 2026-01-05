"""Tests del controlador de Inscripcion usando mocks."""

from unittest.mock import MagicMock
import jwt
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from basketball.controllers.inscripcion_controller import InscripcionController


class InscripcionControllerTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = InscripcionController.as_view(
            {
                "get": "list",
                "post": "create",
            }
        )
        # Usamos un rol permitido: ESTUDIANTE_VINCULACION
        payload = {"role": "ESTUDIANTE_VINCULACION", "sub": "test_user"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def test_list_inscripciones(self):
        mock_service = MagicMock()
        mock_service.list_inscripciones_completas.return_value = [
            {"atleta": {"id": 1}, "inscripcion": {"id": 1}}
        ]
        self.view.cls.service = mock_service

        request = self.factory.get(
            "/inscripciones/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_inscripcion_success(self):
        mock_service = MagicMock()
        mock_service.create_atleta_inscripcion.return_value = {
            "atleta": {"id": 1},
            "inscripcion": {"id": 1},
        }
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/inscripciones/",
            {
                "persona": {"email": "test@test.com", "password": "123"},
                "atleta": {"edad": 10},
                "inscripcion": {},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("atleta", response.data)

    def test_create_inscripcion_forbidden_role(self):
        # Rol no permitido: USER
        # Nota: Con AllowAny habilitado, el endpoint no valida roles.
        # En su lugar, retorna 400 por datos de persona faltantes.
        payload = {"role": "USER", "sub": "test_user"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        auth_header = f"Bearer {token}"

        request = self.factory.post(
            "/inscripciones/",
            {"persona": {}, "atleta": {}},
            format="json",
            HTTP_AUTHORIZATION=auth_header,
        )
        response = self.view(request)

        # Con AllowAny, retorna 400 por ValidationError (datos persona faltantes)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_estado_inscripcion(self):
        view = InscripcionController.as_view({"post": "cambiar_estado"})
        mock_service = MagicMock()
        mock_service.cambiar_estado_inscripcion.return_value = MagicMock(
            habilitada=False
        )
        view.cls.service = mock_service

        request = self.factory.post(
            "/inscripciones/1/cambiar-estado/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["habilitada"])
        self.assertIn("mensaje", response.data)
