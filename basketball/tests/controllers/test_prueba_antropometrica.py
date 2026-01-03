"""Tests del controlador de Prueba Antropométrica usando mocks."""

import jwt
from datetime import date
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
