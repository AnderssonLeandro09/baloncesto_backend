"""Tests del controlador de Prueba Física usando mocks."""

import jwt
from unittest.mock import MagicMock
from django.conf import settings
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory
from ...controllers.prueba_fisica_controller import PruebaFisicaController


class PruebaFisicaControllerTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_list_create = PruebaFisicaController.as_view(
            {"get": "list", "post": "create"}
        )
        self.view_detail = PruebaFisicaController.as_view(
            {"get": "retrieve", "put": "update"}
        )
        self.view_toggle = PruebaFisicaController.as_view({"patch": "toggle_estado"})
        self.view_by_atleta = PruebaFisicaController.as_view({"get": "by_atleta"})
        self.view_atletas_habilitados = PruebaFisicaController.as_view(
            {"get": "atletas_habilitados"}
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
        mock_service.get_all_pruebas_fisicas.return_value = []

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-fisicas/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            PruebaFisicaController.service = original_service

    def test_create_prueba_success(self):
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta.id = 1
        mock_prueba.fecha_registro = "2023-10-27"
        mock_prueba.tipo_prueba = "FUERZA"
        mock_prueba.resultado = 50.0
        mock_prueba.unidad_medida = "kg"
        mock_prueba.observaciones = "Ok"
        mock_prueba.estado = True

        mock_service.create_prueba_fisica.return_value = mock_prueba

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        payload = {
            "atleta_id": 1,
            "fecha_registro": "2023-10-27",
            "tipo_prueba": "FUERZA",
            "resultado": 50.0,
            "unidad_medida": "kg",
            "observaciones": "Ok",
        }

        try:
            request = self.factory.post(
                "/pruebas-fisicas/",
                payload,
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_estudiante}",
            )
            response = self.view_list_create(request)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finally:
            PruebaFisicaController.service = original_service

    def test_permission_denied(self):
        request = self.factory.get(
            "/pruebas-fisicas/", HTTP_AUTHORIZATION=f"Bearer {self.token_invalid}"
        )
        response = self.view_list_create(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_estado_success(self):
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_prueba.atleta.id = 1
        mock_prueba.fecha_registro = "2023-10-27"
        mock_prueba.tipo_prueba = "FUERZA"
        mock_prueba.resultado = 50.0
        mock_prueba.unidad_medida = "kg"
        mock_prueba.observaciones = "Ok"
        mock_prueba.estado = False
        mock_service.toggle_estado.return_value = mock_prueba
        mock_service.get_prueba_fisica_completa.return_value = {
            "id": 1,
            "estado": False,
            "tipo_prueba": "FUERZA",
            "resultado": 50.0,
        }

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.patch(
                "/pruebas-fisicas/1/toggle-estado/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_toggle(request, pk=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["estado"], False)
        finally:
            PruebaFisicaController.service = original_service

    def test_get_by_atleta_success(self):
        mock_service = MagicMock()
        mock_service.get_pruebas_by_atleta_completas.return_value = []

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-fisicas/atleta/1/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_by_atleta(request, atleta_id=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIsInstance(response.data, list)
        finally:
            PruebaFisicaController.service = original_service

    def test_retrieve_success(self):
        mock_service = MagicMock()
        mock_service.get_prueba_fisica_completa.return_value = {"id": 1}

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-fisicas/1/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_detail(request, pk=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            PruebaFisicaController.service = original_service

    def test_update_success(self):
        mock_service = MagicMock()
        mock_prueba = MagicMock()
        mock_prueba.id = 1
        mock_service.update_prueba_fisica.return_value = mock_prueba
        mock_service.get_prueba_fisica_completa.return_value = {"id": 1}

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.put(
                "/pruebas-fisicas/1/",
                {"resultado": 60.0},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_detail(request, pk=1)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        finally:
            PruebaFisicaController.service = original_service

    def test_get_atletas_habilitados_success(self):
        mock_service = MagicMock()
        mock_service.get_atletas_habilitados_con_persona.return_value = [
            {"id": 1, "persona": {"nombre": "Test"}}
        ]

        original_service = PruebaFisicaController.service
        PruebaFisicaController.service = mock_service

        try:
            request = self.factory.get(
                "/pruebas-fisicas/atletas-habilitados/",
                HTTP_AUTHORIZATION=f"Bearer {self.token_entrenador}",
            )
            response = self.view_atletas_habilitados(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
        finally:
            PruebaFisicaController.service = original_service
