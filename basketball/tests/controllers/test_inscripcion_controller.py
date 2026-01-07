"""Tests del controlador de Inscripcion usando mocks."""

from unittest.mock import patch, MagicMock
import jwt
from django.conf import settings
# AJUSTE SENIOR: Usar ValidationError de rest_framework para que el Exception Handler de DRF
# lo capture automáticamente y devuelva 400 con el formato de error correcto.
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from basketball.controllers.inscripcion_controller import InscripcionController


@patch("basketball.controllers.inscripcion_controller.get_user_module_token", return_value="mock_token")
@patch("basketball.controllers.inscripcion_controller.InscripcionService")
class InscripcionControllerTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # Creamos la vista básica para list y create
        self.view = InscripcionController.as_view(
            {
                "get": "list",
                "post": "create",
            }
        )
        # Usamos un rol permitido para las pruebas base: ESTUDIANTE_VINCULACION
        payload = {"role": "ESTUDIANTE_VINCULACION", "sub": "test_user"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def test_list_inscripciones(self, mock_service_class, mock_token):
        """Verifica que se listen las inscripciones correctamente usando el servicio mockeado."""
        mock_service = mock_service_class.return_value
        # Inyectamos el mock directamente en el controlador para asegurar robustez
        InscripcionController.service = mock_service

        mock_service.list_inscripciones_completas.return_value = [
            {"atleta": {"id": 1}, "inscripcion": {"id": 1}}
        ]

        request = self.factory.get("/inscripciones/", HTTP_AUTHORIZATION=self.auth_header)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        mock_service.list_inscripciones_completas.assert_called_once_with("mock_token")

    def test_create_inscripcion_success(self, mock_service_class, mock_token):
        """Prueba la creación exitosa de un atleta e inscripción."""
        mock_service = mock_service_class.return_value
        InscripcionController.service = mock_service

        mock_service.create_atleta_inscripcion.return_value = {
            "atleta": {"id": 1},
            "inscripcion": {"id": 1},
        }

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
        self.assertTrue(mock_service.create_atleta_inscripcion.called)

    def test_create_inscripcion_duplicate_cedula(self, mock_service_class, mock_token):
        """Verifica que falle si el atleta ya existe lanzando un ValidationError."""
        mock_service = mock_service_class.return_value
        InscripcionController.service = mock_service

        mensaje_error = "El atleta ya se encuentra registrado"
        mock_service.create_atleta_inscripcion.side_effect = ValidationError(mensaje_error)

        request = self.factory.post(
            "/inscripciones/",
            {
                "persona": {"email": "duplicate@test.com", "password": "123"},
                "atleta": {"cedula": "1234567890"},
                "inscripcion": {},
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        # Validamos que el controlador capture el ValidationError y devuelva 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(mensaje_error, response.data["detail"])

    def test_create_inscripcion_forbidden_role(self, mock_service_class, mock_token):
        """
        Verifica el comportamiento con un rol no autorizado.
        Nota: Según la configuración actual (AllowAny), el permiso pasa, pero 
        la solicitud debe fallar por validación de datos (HTTP 400).
        Si se protege el endpoint, este test debería esperar HTTP 403.
        """
        payload = {"role": "USER", "sub": "test_user"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        auth_header = f"Bearer {token}"

        request = self.factory.post(
            "/inscripciones/",
            {"persona": {}, "atleta": {}},  # Datos insuficientes
            format="json",
            HTTP_AUTHORIZATION=auth_header,
        )
        response = self.view(request)

        # Comportamiento esperado bajo AllowAny: Error de validación de datos
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_estado_inscripcion(self, mock_service_class, mock_token):
        """Verifica la acción de cambio de estado (toggle) de la inscripción."""
        mock_service = mock_service_class.return_value
        InscripcionController.service = mock_service

        view = InscripcionController.as_view({"post": "cambiar_estado"})
        mock_service.cambiar_estado_inscripcion.return_value = MagicMock(habilitada=False)

        request = self.factory.post(
            "/inscripciones/1/cambiar-estado/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["habilitada"])
        self.assertIn("mensaje", response.data)

    @patch("basketball.controllers.inscripcion_controller.Inscripcion.objects.filter")
    def test_verificar_cedula_endpoint(self, mock_filter, mock_service_class, mock_token):
        """Verifica la acción personalizada GET /verificar-cedula/."""
        # Simulamos que el DNI ya existe en la base de datos
        mock_filter.return_value.exists.return_value = True

        view = InscripcionController.as_view({"get": "verificar_cedula"})
        request = self.factory.get(
            "/inscripciones/verificar-cedula/",
            {"dni": "1234567890"},
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["existe"])
        self.assertEqual(response.data["mensaje"], "El atleta ya se encuentra registrado")
