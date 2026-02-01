"""Tests del controlador de GrupoAtleta usando mocks."""

import jwt
from django.conf import settings
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from basketball.controllers.grupo_atleta_controller import GrupoAtletaController


class GrupoAtletaControllerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view(
            {
                "get": "list",
                "post": "create",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        )
        # Token para Entrenador
        payload = {"role": "ENTRENADOR", "sub": "test_entrenador"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def test_list_returns_data(self):
        mock_service = MagicMock()
        # Simulamos retorno de objetos (aunque el controller los serializa)
        mock_grupo = MagicMock()
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo A"
        mock_grupo.rango_edad_minima = 10
        mock_grupo.rango_edad_maxima = 12
        mock_grupo.categoria = "Infantil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        # Mock atletas.all() para el serializer
        mock_grupo.atletas.all.return_value = []

        mock_service.list_grupos_by_user.return_value = [mock_grupo]
        self.view.cls.service = mock_service

        request = self.factory.get(
            "/grupos-atletas/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": [...], ...}
        data = response.data.get("data", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["nombre"], "Grupo A")

    @patch("basketball.controllers.grupo_atleta_controller.GrupoAtletaSerializer")
    def test_create_success(self, mock_serializer_class):
        # Mock del serializer para saltar validación de atletas
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            "nombre": "Nuevo Grupo",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 15,
            "categoria": "Juvenil",
            "atletas": [1, 2],
        }
        mock_serializer_class.return_value = mock_serializer

        mock_service = MagicMock()
        mock_grupo = MagicMock()
        mock_grupo.id = 1
        mock_grupo.nombre = "Nuevo Grupo"
        mock_grupo.rango_edad_minima = 10
        mock_grupo.rango_edad_maxima = 15
        mock_grupo.categoria = "Juvenil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1

        # Simular atletas.all() para el response serializer
        mock_atleta1 = MagicMock()
        mock_atleta1.id = 1
        mock_atleta1.pk = 1
        mock_atleta1.persona_external = "ext-1"
        mock_atleta1.edad = 15
        mock_atleta1.sexo = "M"

        mock_atleta2 = MagicMock()
        mock_atleta2.id = 2
        mock_atleta2.pk = 2
        mock_atleta2.persona_external = "ext-2"
        mock_atleta2.edad = 14
        mock_atleta2.sexo = "F"

        mock_grupo.atletas.all.return_value = [mock_atleta1, mock_atleta2]

        mock_service.create_grupo.return_value = mock_grupo
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/grupos-atletas/",
            {
                "nombre": "Nuevo Grupo",
                "rango_edad_minima": 10,
                "rango_edad_maxima": 15,
                "categoria": "Juvenil",
                "atletas": [1, 2],
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": {...}, ...}
        data = response.data.get("data", response.data)
        self.assertEqual(data["nombre"], "Nuevo Grupo")

    def test_atletas_elegibles_grupo(self):
        view = GrupoAtletaController.as_view({"get": "atletas_elegibles_grupo"})
        mock_service = MagicMock()
        mock_atleta = MagicMock()
        mock_atleta.id = 1

        mock_service.list_atletas_elegibles.return_value = [mock_atleta]
        view.cls.service = mock_service

        request = self.factory.get(
            "/grupos-atletas/1/atletas-elegibles/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": [...], ...}
        data = response.data.get("data", response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], 1)

    @patch("basketball.controllers.grupo_atleta_controller.GrupoAtletaSerializer")
    def test_create_handles_error(self, mock_serializer_class):
        from django.core.exceptions import ValidationError

        # Mock del serializer
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            "nombre": "Grupo Error",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 15,
            "categoria": "Juvenil",
        }
        mock_serializer_class.return_value = mock_serializer

        mock_service = MagicMock()
        mock_service.create_grupo.side_effect = ValidationError("Error de negocio")
        self.view.cls.service = mock_service

        request = self.factory.post(
            "/grupos-atletas/",
            {
                "nombre": "Grupo Error",
                "rango_edad_minima": 10,
                "rango_edad_maxima": 15,
                "categoria": "Juvenil",
            },
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("msg", response.data)

    def test_retrieve_not_found(self):
        view = GrupoAtletaController.as_view({"get": "retrieve"})
        mock_service = MagicMock()
        mock_service.get_grupo.return_value = None
        view.cls.service = mock_service

        request = self.factory.get(
            "/grupos-atletas/99/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=99)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("basketball.controllers.grupo_atleta_controller.GrupoAtletaSerializer")
    def test_update_success(self, mock_serializer_class):
        # Mock del serializer
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"nombre": "Grupo Actualizado"}
        mock_serializer_class.return_value = mock_serializer

        view = GrupoAtletaController.as_view({"put": "update"})
        mock_service = MagicMock()
        mock_grupo = MagicMock()
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Actualizado"
        mock_grupo.rango_edad_minima = 10
        mock_grupo.rango_edad_maxima = 15
        mock_grupo.categoria = "Juvenil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = []

        mock_service.get_grupo.return_value = mock_grupo
        mock_service.update_grupo.return_value = mock_grupo
        view.cls.service = mock_service

        request = self.factory.put(
            "/grupos-atletas/1/",
            {"nombre": "Grupo Actualizado"},
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La respuesta tiene estructura envolvente {"msg": ..., "data": {...}, ...}
        data = response.data.get("data", response.data)
        self.assertEqual(data["nombre"], "Grupo Actualizado")

    def test_destroy_success(self):
        view = GrupoAtletaController.as_view({"delete": "destroy"})
        mock_service = MagicMock()
        mock_service.delete_grupo.return_value = True
        view.cls.service = mock_service

        request = self.factory.delete(
            "/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_forbidden_for_estudiante(self):
        # Token para Estudiante
        payload = {"role": "ESTUDIANTE_VINCULACION", "sub": "test_estudiante"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        auth_header = f"Bearer {token}"

        request = self.factory.get("/grupos-atletas/", HTTP_AUTHORIZATION=auth_header)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
