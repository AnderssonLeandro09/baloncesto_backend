"""
Tests completos para la baja (eliminación lógica) de Grupos de Atletas usando mocks.

Estos tests usan el service real para validar todas las reglas de negocio,
solo se mockean las dependencias externas (DAO, modelos, user_module).
"""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings

from basketball.controllers.grupo_atleta_controller import GrupoAtletaController
from basketball.services.grupo_atleta_service import GrupoAtletaService
from basketball.models import GrupoAtleta, Entrenador


class TestGrupoAtletaBaja(SimpleTestCase):
    """Tests para la baja (eliminación lógica) de grupos de atletas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view({"delete": "destroy"})

        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de baja exitosa
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_grupo_atleta_completo_exitoso(self, mock_entrenador_objects):
        """Test: Dar de baja un grupo de atletas correctamente."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo a Eliminar"
        mock_grupo.entrenador_id = 1
        mock_grupo.eliminado = False

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()

        def get_by_id_side_effect(id_pedido):
            if int(id_pedido) == mock_grupo.id:
                return mock_grupo
            return None

        real_service.dao.get_by_id_activo.side_effect = get_by_id_side_effect
        real_service.dao.update.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        real_service.dao.get_by_id_activo.assert_called_once_with(1)
        real_service.dao.update.assert_called_once_with(1, eliminado=True)

    # =========================================================================
    # Tests de grupo no existe
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_grupo_inexistente_retorna_404(self, mock_entrenador_objects):
        """Test: Retorna 404 cuando el grupo no existe."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id_activo.return_value = None
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/999/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_grupo_ya_eliminado_retorna_404(self, mock_entrenador_objects):
        """Test: Retorna 404 cuando el grupo ya fue eliminado (baja lógica)."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id_activo.return_value = None
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # Tests sin permiso (ownership)
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_grupo_de_otro_entrenador_falla(self, mock_entrenador_objects):
        """Test: Falla cuando un entrenador intenta eliminar el grupo de otro."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 2
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo de Otro Entrenador"
        mock_grupo.entrenador_id = 1  # Pertenece a otro entrenador
        mock_grupo.eliminado = False

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("permiso", response.data["error"].lower())

    # =========================================================================
    # Tests con ID inválido
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_con_id_negativo_falla(self, mock_entrenador_objects):
        """Test: Falla cuando se proporciona un ID negativo."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/-1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=-1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_con_id_cero_falla(self, mock_entrenador_objects):
        """Test: Falla cuando se proporciona ID cero."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        GrupoAtletaController.service = real_service

        request = self.factory.delete(
            "/api/grupos-atletas/0/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=0)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_dar_baja_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        request = self.factory.delete("/api/grupos-atletas/1/")
        response = self.view(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
