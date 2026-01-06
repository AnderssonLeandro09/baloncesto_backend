"""Tests del controlador de Prueba Antropométrica usando mocks."""

import jwt
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from django.conf import settings
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from ...controllers.prueba_antropometrica_controller import (
    PruebaAntropometricaController,
)


class PruebaAntropometricaControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.view_list_create = PruebaAntropometricaController.as_view(
            {"get": "list", "post": "create"}
        )
        self.view_detail = PruebaAntropometricaController.as_view(
            {"get": "retrieve", "put": "update"}
        )
        self.view_toggle = PruebaAntropometricaController.as_view(
            {"patch": "toggle_estado"}
        )
        self.view_by_atleta = PruebaAntropometricaController.as_view(
            {"get": "by_atleta"}
        )

        self.token_entrenador = self._get_token("ENTRENADOR")
        self.token_estudiante = self._get_token("ESTUDIANTE_VINCULACION")
        self.token_invalid = self._get_token("OTRO_ROL")

    def _get_token(self, role):
        payload = {
            "sub": "123",
            "role": role,
            "email": "test@test.com",
            "name": "Test User",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    def test_list_pruebas_success(self):
        mock_service = MagicMock()
        mock_service.get_all_pruebas_antropometricas.return_value = []

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-antropometricas/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(response.data, list)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_create_prueba_success(self):
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = "2023-10-27"
        mock_prueba.peso = 70.5
        mock_prueba.estatura = 1.75
        mock_prueba.altura_sentado = 0.90
        mock_prueba.envergadura = 1.80
        mock_prueba.indice_masa_corporal = 23.02
        mock_prueba.indice_cormico = 51.43
        mock_prueba.observaciones = "Ok"
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": "2023-10-27",
            "peso": 70.5,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
            "observaciones": "Ok",
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_estudiante}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_permission_denied(self):
        request = self.factory.get(
            "/pruebas-antropometricas/",
            HTTP_AUTHORIZATION=f"Bearer {self.token_invalid}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_estado_success(self):
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.estado = False
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.registrado_por = "Entrenador Test"
        mock_prueba.rol_registrador = "ENTRENADOR"
        mock_prueba.fecha_registro = date.today()
        mock_prueba.peso = Decimal("48.5")
        mock_prueba.estatura = Decimal("1.55")
        mock_prueba.altura_sentado = Decimal("0.82")
        mock_prueba.envergadura = Decimal("1.60")
        mock_prueba.indice_masa_corporal = Decimal("20.18")
        mock_prueba.indice_cormico = Decimal("52.90")
        mock_prueba.observaciones = "Test"

        mock_service.toggle_estado.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        try:
            request = self.factory.patch(
                "/pruebas-antropometricas/1/toggle-estado/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_toggle(request, pk=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["estado"], False)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_get_by_atleta_success(self):
        mock_service = MagicMock()
        mock_service.get_pruebas_antropometricas_by_atleta.return_value = []

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-antropometricas/atleta/1/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_by_atleta(request, atleta_id=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(response.data, list)
        finally:
            PruebaAntropometricaController.service = original_service

    # ========================================================================
    # Tests de validación de peso
    # ========================================================================
    
    def test_create_prueba_peso_negativo(self):
        """Test que valida rechazo de peso negativo."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": -10.5,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peso", response.data)

    def test_create_prueba_peso_cero(self):
        """Test que valida rechazo de peso en cero."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peso", response.data)

    def test_create_prueba_peso_muy_bajo(self):
        """Test que valida rechazo de peso < 20 kg."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 15.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peso", response.data)

    def test_create_prueba_peso_exorbitante(self):
        """Test que valida rechazo de peso > 200 kg."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 250.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("peso", response.data)

    def test_create_prueba_peso_limite_inferior_valido(self):
        """Test que valida aceptación de peso mínimo válido (20 kg)."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = date.today().isoformat()
        mock_prueba.peso = 20.0
        mock_prueba.estatura = 1.20
        mock_prueba.altura_sentado = 0.65
        mock_prueba.envergadura = 1.25
        mock_prueba.indice_masa_corporal = 13.89
        mock_prueba.indice_cormico = 54.17
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 20.0,
            "estatura": 1.20,
            "altura_sentado": 0.65,
            "envergadura": 1.25,
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_create_prueba_peso_limite_superior_valido(self):
        """Test que valida aceptación de peso máximo válido (200 kg)."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = date.today().isoformat()
        mock_prueba.peso = 200.0
        mock_prueba.estatura = 2.20
        mock_prueba.altura_sentado = 1.15
        mock_prueba.envergadura = 2.40
        mock_prueba.indice_masa_corporal = 41.32
        mock_prueba.indice_cormico = 52.27
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 200.0,
            "estatura": 2.20,
            "altura_sentado": 1.15,
            "envergadura": 2.40,
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    # ========================================================================
    # Tests de validación de estatura
    # ========================================================================

    def test_create_prueba_estatura_negativa(self):
        """Test que valida rechazo de estatura negativa."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": -1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estatura", response.data)

    def test_create_prueba_estatura_muy_baja(self):
        """Test que valida rechazo de estatura < 1.0 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 30.0,
            "estatura": 0.85,
            "altura_sentado": 0.50,
            "envergadura": 0.90,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estatura", response.data)

    def test_create_prueba_estatura_exorbitante(self):
        """Test que valida rechazo de estatura > 2.5 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 150.0,
            "estatura": 3.0,
            "altura_sentado": 1.40,
            "envergadura": 3.20,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estatura", response.data)

    # ========================================================================
    # Tests de validación de altura_sentado
    # ========================================================================

    def test_create_prueba_altura_sentado_negativa(self):
        """Test que valida rechazo de altura sentado negativa."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": -0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("altura_sentado", response.data)

    def test_create_prueba_altura_sentado_muy_baja(self):
        """Test que valida rechazo de altura sentado < 0.5 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.30,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("altura_sentado", response.data)

    def test_create_prueba_altura_sentado_muy_alta(self):
        """Test que valida rechazo de altura sentado > 1.5 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 1.60,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("altura_sentado", response.data)

    def test_create_prueba_altura_sentado_mayor_que_estatura(self):
        """Test que valida rechazo de altura_sentado > estatura."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 1.85,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("altura_sentado", response.data)

    def test_create_prueba_altura_sentado_desproporcionada(self):
        """Test que valida rechazo de altura_sentado < 40% de estatura."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.60,  # 34% de 1.75, muy bajo
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("altura_sentado", response.data)

    # ========================================================================
    # Tests de validación de envergadura
    # ========================================================================

    def test_create_prueba_envergadura_negativa(self):
        """Test que valida rechazo de envergadura negativa."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": -1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("envergadura", response.data)

    def test_create_prueba_envergadura_muy_baja(self):
        """Test que valida rechazo de envergadura < 1.0 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 0.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("envergadura", response.data)

    def test_create_prueba_envergadura_exorbitante(self):
        """Test que valida rechazo de envergadura > 3.0 m."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 3.50,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("envergadura", response.data)

    def test_create_prueba_envergadura_desproporcionada_baja(self):
        """Test que valida rechazo de ratio envergadura/estatura < 0.9."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 2.00,
            "altura_sentado": 1.05,
            "envergadura": 1.70,  # ratio = 0.85, muy bajo
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("envergadura", response.data)

    def test_create_prueba_envergadura_desproporcionada_alta(self):
        """Test que valida rechazo de ratio envergadura/estatura > 1.4."""
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 2.60,  # ratio = 1.49, muy alto
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("envergadura", response.data)

    # ========================================================================
    # Tests de validación de fecha
    # ========================================================================

    def test_create_prueba_fecha_futura(self):
        """Test que valida rechazo de fechas futuras."""
        fecha_futura = date.today() + timedelta(days=30)
        payload = {
            "atleta_id": 1,
            "fecha_registro": fecha_futura.isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_registro", response.data)

    def test_create_prueba_fecha_muy_antigua(self):
        """Test que valida rechazo de fechas > 10 años en el pasado."""
        fecha_antigua = date.today() - timedelta(days=365 * 11)
        payload = {
            "atleta_id": 1,
            "fecha_registro": fecha_antigua.isoformat(),
            "peso": 70.0,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        request = self.factory.post(
            "/pruebas-antropometricas/",
            payload,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_registro", response.data)

    def test_create_prueba_fecha_hoy_valida(self):
        """Test que valida aceptación de fecha actual."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = date.today().isoformat()
        mock_prueba.peso = 70.5
        mock_prueba.estatura = 1.75
        mock_prueba.altura_sentado = 0.90
        mock_prueba.envergadura = 1.80
        mock_prueba.indice_masa_corporal = 23.02
        mock_prueba.indice_cormico = 51.43
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70.5,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_create_prueba_fecha_limite_valida(self):
        """Test que valida aceptación de fecha en el límite (10 años atrás)."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        fecha_limite = date.today() - timedelta(days=365 * 10 - 1)
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = fecha_limite.isoformat()
        mock_prueba.peso = 70.5
        mock_prueba.estatura = 1.75
        mock_prueba.altura_sentado = 0.90
        mock_prueba.envergadura = 1.80
        mock_prueba.indice_masa_corporal = 23.02
        mock_prueba.indice_cormico = 51.43
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": fecha_limite.isoformat(),
            "peso": 70.5,
            "estatura": 1.75,
            "altura_sentado": 0.90,
            "envergadura": 1.80,
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    # ========================================================================
    # Tests de conversión de enteros a decimales
    # ========================================================================

    def test_create_prueba_con_enteros_sin_punto(self):
        """Test que valida conversión automática de enteros a decimales."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = date.today().isoformat()
        mock_prueba.peso = 70.0
        mock_prueba.estatura = 2.0
        mock_prueba.altura_sentado = 1.0
        mock_prueba.envergadura = 2.0
        mock_prueba.indice_masa_corporal = 17.5
        mock_prueba.indice_cormico = 50.0
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        # Enviar valores enteros sin punto decimal
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": 70,  # entero
            "estatura": 2,  # entero
            "altura_sentado": 1,  # entero
            "envergadura": 2,  # entero
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service

    def test_create_prueba_con_strings_numericos(self):
        """Test que valida conversión de strings numéricos a decimales."""
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta = "Atleta Test"
        mock_prueba.fecha_registro = date.today().isoformat()
        mock_prueba.peso = 75.5
        mock_prueba.estatura = 1.80
        mock_prueba.altura_sentado = 0.95
        mock_prueba.envergadura = 1.85
        mock_prueba.indice_masa_corporal = 23.3
        mock_prueba.indice_cormico = 52.8
        mock_prueba.estado = True

        mock_service.create_prueba_antropometrica.return_value = mock_prueba

        original_service = PruebaAntropometricaController.service
        PruebaAntropometricaController.service = mock_service

        # Enviar valores como strings
        payload = {
            "atleta_id": 1,
            "fecha_registro": date.today().isoformat(),
            "peso": "75.5",
            "estatura": "1.80",
            "altura_sentado": "0.95",
            "envergadura": "1.85",
        }

        try:
            request = self.factory.post(
                "/pruebas-antropometricas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaAntropometricaController.service = original_service
