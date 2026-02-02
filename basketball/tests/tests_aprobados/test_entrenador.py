"""Tests del controlador de Entrenador usando mocks."""

import jwt
from django.conf import settings
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.entrenador_controller import EntrenadorController


class EntrenadorControllerTests(SimpleTestCase):
    def setUp(self):
        # Mock del token para evitar conexión al módulo externo de usuarios.
        # Así los tests no requieren Docker ni el servicio (puerto 8096).
        self.patcher_token = patch(
            "basketball.controllers.entrenador_controller.get_user_module_token",
            return_value="dummy-token",
        )
        self.patcher_token.start()

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

    def tearDown(self):
        # Detener el mock del token
        self.patcher_token.stop()

    def test_list_returns_data(self):
        # Listado: debe retornar arreglo de entrenadores activos con estado 200.
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
        # Validación positiva: con 'especialidad' y 'club_asignado' presentes,
        # el controlador debe crear el entrenador (201) y devolver el objeto.
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
        # Cuando el servicio lanza una Exception genérica, el controlador
        # responde 400 y expone el mensaje de error.
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
        self.assertEqual(response.data.get("error"), "bad")

    def test_create_fails_when_especialidad_vacia(self):
        # Validación: 'especialidad' es requerida y no puede estar vacía.
        # Si viene vacía, el servicio lanza ValidationError y el controlador
        # debe responder 400 con el mensaje correspondiente.
        """Debe responder 400 si especialidad está vacía."""
        mock_service = MagicMock()
        mock_service.create_entrenador.side_effect = ValidationError(
            "especialidad y club_asignado son obligatorios"
        )
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/entrenadores/",
            {
                "persona": {
                    "first_name": "A",
                    "email": "test@unl.edu.ec",
                    "password": "password123",
                },
                "entrenador": {"especialidad": "", "club_asignado": "Club A"},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        err = response.data.get("error")
        self.assertIn("especialidad y club_asignado son obligatorios", str(err))

    def test_create_fails_when_club_asignado_vacio(self):
        # Validación: 'club_asignado' es requerido y no puede estar vacío.
        # Si viene vacío, el servicio lanza ValidationError y el controlador
        # debe responder 400 con el mensaje correspondiente.
        """Debe responder 400 si club_asignado está vacío."""
        mock_service = MagicMock()
        mock_service.create_entrenador.side_effect = ValidationError(
            "especialidad y club_asignado son obligatorios"
        )
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/entrenadores/",
            {
                "persona": {
                    "first_name": "A",
                    "email": "test@unl.edu.ec",
                    "password": "password123",
                },
                "entrenador": {"especialidad": "Táctica", "club_asignado": ""},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        err = response.data.get("error")
        self.assertIn("especialidad y club_asignado son obligatorios", str(err))

    def test_create_shows_specific_message_from_validationerror(self):
        # Propagación de errores: el controlador debe incluir exactamente
        # el mensaje del ValidationError que retorna el servicio.
        """Debe mostrar el mensaje exacto de ValidationError del servicio."""
        mock_service = MagicMock()
        mock_service.create_entrenador.side_effect = ValidationError(
            "La especialidad es requerida y no puede estar vacía"
        )
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/entrenadores/",
            {
                "persona": {
                    "first_name": "A",
                    "email": "test@unl.edu.ec",
                    "password": "password123",
                },
                "entrenador": {"especialidad": "", "club_asignado": "Club A"},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        err = response.data.get("error")
        self.assertIn("La especialidad es requerida y no puede estar vacía", str(err))

    def test_retrieve_not_found(self):
        # Recuperación: si el entrenador no existe o está eliminado, debe retornar 404.
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
        # Actualización: permite cambiar 'especialidad' y responde 200
        # devolviendo el valor actualizado.
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
        # Eliminación lógica: retorna 204 No Content cuando el borrado lógico es exitoso.
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
        # Permisos: solo rol ADMIN puede acceder; rol USER debe recibir 403 Forbidden.
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
