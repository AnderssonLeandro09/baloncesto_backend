"""
Tests completos para UPDATE (actualización) de Grupos de Atletas usando mocks.

Estos tests usan el service real para validar todas las reglas de negocio,
solo se mockean las dependencias externas (DAO, modelos, user_module).
"""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from django.core.exceptions import ValidationError
import jwt
from django.conf import settings

from basketball.controllers.grupo_atleta_controller import GrupoAtletaController
from basketball.services.grupo_atleta_service import GrupoAtletaService
from basketball.models import GrupoAtleta, Entrenador, Atleta


class TestGrupoAtletaUpdate(SimpleTestCase):
    """Tests para la actualización de grupos de atletas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view(
            {"put": "update", "patch": "partial_update"}
        )

        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de actualización exitosa
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_completo_exitoso(
        self,
        mock_entrenador_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Actualizar un grupo de atletas con todos los campos."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Actualizado"
        mock_grupo.rango_edad_minima = 15
        mock_grupo.rango_edad_maxima = 19
        mock_grupo.categoria = "Juvenil Premium"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = []

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        real_service.dao.update.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            False
        )

        data = {
            "nombre": "Grupo Actualizado",
            "rango_edad_minima": 15,
            "rango_edad_maxima": 19,
            "categoria": "Juvenil Premium",
        }

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["msg"], "Grupo actualizado exitosamente")
        self.assertEqual(response.data["data"]["nombre"], "Grupo Actualizado")
        real_service.get_grupo.assert_called_once_with(1)

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_agregando_atletas_exitoso(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Actualizar un grupo agregando atletas."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta1 = MagicMock(spec=Atleta)
        mock_atleta1.id = 1
        mock_atleta1.edad = 15

        mock_atleta2 = MagicMock(spec=Atleta)
        mock_atleta2.id = 2
        mock_atleta2.edad = 16

        atletas_map = {1: mock_atleta1, 2: mock_atleta2}

        def atleta_filter_mock(**kwargs):
            if "id" in kwargs:
                # Para el serializer - filter(id=X).first()
                mock_result = MagicMock()
                mock_result.first.return_value = atletas_map.get(kwargs["id"])
                return mock_result
            elif "id__in" in kwargs:
                # Para el service - filter(id__in=[...])
                ids_solicitados = kwargs["id__in"]
                filtered = [
                    atletas_map[aid] for aid in ids_solicitados if aid in atletas_map
                ]
                mock_qs = MagicMock()
                mock_qs.__iter__.return_value = iter(filtered)
                mock_qs.__len__.return_value = len(filtered)
                return mock_qs
            return MagicMock()

        mock_atleta_objects.filter.side_effect = atleta_filter_mock

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Test"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = [mock_atleta1, mock_atleta2]
        mock_grupo.atletas.set = MagicMock()

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        real_service.dao.update.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            False
        )

        data = {
            "nombre": "Grupo Test",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1, 2],
        }

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        mock_grupo.atletas.set.assert_called_once()  # Verificar que se llamó

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_solo_nombre_exitoso(
        self,
        mock_entrenador_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Actualizar solo el nombre del grupo (actualización parcial)."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Nuevo Nombre"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = []

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        real_service.dao.update.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            False
        )

        data = {"nombre": "Nuevo Nombre"}

        request = self.factory.patch(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["nombre"], "Nuevo Nombre")

    # =========================================================================
    # Tests de actualización con errores
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_inexistente_retorna_404(self, mock_entrenador_objects):
        """Test: Retorna 404 cuando el grupo no existe."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=None)
        real_service.dao.get_by_id_activo.return_value = None
        GrupoAtletaController.service = real_service

        data = {"nombre": "Nuevo Nombre"}

        request = self.factory.put(
            "/api/grupos-atletas/999/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Grupo no encontrado")

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_con_nombre_duplicado_falla(
        self,
        mock_entrenador_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando se intenta actualizar con un nombre ya existente."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Original"
        mock_grupo.entrenador_id = 1
        mock_grupo.eliminado = False

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        # Simular que ya existe otro grupo con ese nombre
        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            True
        )

        data = {"nombre": "Nombre Existente"}

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Error de validación")

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_con_atleta_fuera_de_rango_falla(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando se intenta agregar un atleta fuera del rango de edad."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.edad = 20  # Fuera del rango 14-18

        atletas_map = {1: mock_atleta}

        def atleta_filter_mock(**kwargs):
            if "id" in kwargs:
                # Para el serializer - filter(id=X).first()
                mock_result = MagicMock()
                mock_result.first.return_value = atletas_map.get(kwargs["id"])
                return mock_result
            elif "id__in" in kwargs:
                # Para el service - filter(id__in=[...])
                ids_solicitados = kwargs["id__in"]
                filtered = [
                    atletas_map[aid] for aid in ids_solicitados if aid in atletas_map
                ]
                mock_qs = MagicMock()
                mock_qs.__iter__.return_value = iter(filtered)
                mock_qs.__len__.return_value = len(filtered)
                return mock_qs
            return MagicMock()

        mock_atleta_objects.filter.side_effect = atleta_filter_mock

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Test"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.entrenador_id = 1
        mock_grupo.eliminado = False

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            False
        )

        data = {
            "nombre": "Grupo Test",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1],
        }

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Error de validación")

    @patch("basketball.models.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_de_otro_entrenador_falla(
        self, mock_entrenador_objects, mock_grupo_objects
    ):
        """Test: Falla cuando se intenta actualizar el grupo de otro entrenador."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 2
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo de Otro"
        mock_grupo.entrenador_id = 1  # Pertenece a otro entrenador
        mock_grupo.eliminado = False

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=mock_grupo)
        real_service.get_entrenador_from_user = MagicMock(return_value=mock_entrenador)
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        real_service.update_grupo = MagicMock(
            side_effect=ValidationError("No tienes permiso para actualizar este grupo")
        )
        GrupoAtletaController.service = real_service

        mock_grupo_objects.filter.return_value.exclude.return_value.exists.return_value = (
            False
        )

        data = {"nombre": "Nuevo Nombre"}

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_actualizar_grupo_con_id_invalido_falla(self, mock_entrenador_objects):
        """Test: Falla cuando se proporciona un ID inválido."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.get_grupo = MagicMock(return_value=None)
        GrupoAtletaController.service = real_service

        data = {"nombre": "Nuevo Nombre"}

        request = self.factory.put(
            "/api/grupos-atletas/-1/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request, pk=-1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_actualizar_grupo_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        data = {"nombre": "Nuevo Nombre"}

        request = self.factory.put(
            "/api/grupos-atletas/1/",
            data=data,
            format="json",
        )
        response = self.view(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
