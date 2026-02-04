"""
Tests completos para GET (list y retrieve) de Grupos de Atletas usando mocks.

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
from basketball.models import GrupoAtleta, Entrenador, Atleta


class TestGrupoAtletaGet(SimpleTestCase):
    """Tests para la obtención (list y retrieve) de grupos de atletas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view_list = GrupoAtletaController.as_view({"get": "list"})
        self.view_retrieve = GrupoAtletaController.as_view({"get": "retrieve"})

        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de list exitosos
    # =========================================================================

    def test_listar_grupos_exitoso(self):
        """Test: Listar todos los grupos del entrenador autenticado."""
        with patch.object(GrupoAtletaController, "service") as mock_service:
            mock_grupo1 = MagicMock(spec=GrupoAtleta)
            mock_grupo1.id = 1
            mock_grupo1.nombre = "Grupo Juvenil A"
            mock_grupo1.rango_edad_minima = 14
            mock_grupo1.rango_edad_maxima = 18
            mock_grupo1.categoria = "Juvenil"
            mock_grupo1.estado = True
            mock_grupo1.eliminado = False
            mock_grupo1.entrenador_id = 1
            mock_grupo1.atletas = MagicMock()
            mock_grupo1.atletas.all.return_value = []

            mock_grupo2 = MagicMock(spec=GrupoAtleta)
            mock_grupo2.id = 2
            mock_grupo2.nombre = "Grupo Infantil B"
            mock_grupo2.rango_edad_minima = 10
            mock_grupo2.rango_edad_maxima = 14
            mock_grupo2.categoria = "Infantil"
            mock_grupo2.estado = True
            mock_grupo2.eliminado = False
            mock_grupo2.entrenador_id = 1
            mock_grupo2.atletas = MagicMock()
            mock_grupo2.atletas.all.return_value = []

            mock_service.list_all_grupos_by_user.return_value = [
                mock_grupo1,
                mock_grupo2,
            ]

            request = self.factory.get(
                "/api/grupos-atletas/", HTTP_AUTHORIZATION=self.auth_header
            )
            response = self.view_list(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertEqual(response.data["msg"], "Grupos listados exitosamente")
            self.assertIsInstance(response.data["data"], list)
            mock_service.list_all_grupos_by_user.assert_called_once()

    def test_listar_grupos_vacio_exitoso(self):
        """Test: Listar grupos cuando el entrenador no tiene ninguno."""
        with patch.object(GrupoAtletaController, "service") as mock_service:
            mock_service.list_all_grupos_by_user.return_value = []

            request = self.factory.get(
                "/api/grupos-atletas/", HTTP_AUTHORIZATION=self.auth_header
            )
            response = self.view_list(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "success")
            self.assertIsInstance(response.data["data"], list)
            self.assertEqual(len(response.data["data"]), 0)
            mock_service.list_all_grupos_by_user.assert_called_once()

    # =========================================================================
    # Tests de retrieve exitosos
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_obtener_grupo_exitoso(self, mock_entrenador_objects):
        """Test: Obtener un grupo específico por ID."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta1 = MagicMock(spec=Atleta)
        mock_atleta1.id = 1
        mock_atleta1.edad = 15

        mock_atleta2 = MagicMock(spec=Atleta)
        mock_atleta2.id = 2
        mock_atleta2.edad = 17

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Juvenil A"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = [mock_atleta1, mock_atleta2]

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id_activo.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        request = self.factory.get(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view_retrieve(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["msg"], "Grupo obtenido exitosamente")
        self.assertEqual(response.data["data"]["nombre"], "Grupo Juvenil A")
        self.assertEqual(response.data["data"]["rango_edad_minima"], 14)
        self.assertEqual(response.data["data"]["rango_edad_maxima"], 18)
        real_service.dao.get_by_id_activo.assert_called_once_with(1)

    # =========================================================================
    # Tests de retrieve con errores
    # =========================================================================

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_obtener_grupo_inexistente_retorna_404(self, mock_entrenador_objects):
        """Test: Retorna 404 cuando el grupo no existe."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id_activo.return_value = None
        GrupoAtletaController.service = real_service

        request = self.factory.get(
            "/api/grupos-atletas/999/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view_retrieve(request, pk=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["msg"], "Grupo no encontrado")

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_obtener_grupo_de_otro_entrenador_falla(self, mock_entrenador_objects):
        """Test: Falla cuando se intenta obtener el grupo de otro entrenador."""
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

        request = self.factory.get(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view_retrieve(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_obtener_grupo_con_id_invalido_falla(self, mock_entrenador_objects):
        """Test: Falla cuando se proporciona un ID inválido."""
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        GrupoAtletaController.service = real_service

        request = self.factory.get(
            "/api/grupos-atletas/-1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view_retrieve(request, pk=-1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_listar_grupos_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        request = self.factory.get("/api/grupos-atletas/")
        response = self.view_list(request)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_obtener_grupo_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        request = self.factory.get("/api/grupos-atletas/1/")
        response = self.view_retrieve(request, pk=1)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
