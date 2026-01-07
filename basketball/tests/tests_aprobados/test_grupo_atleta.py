"""
Tests completos para Grupo de Atleta usando mocks.
Solo incluye los dos casos de prueba completos: creación y dar de baja.

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


class TestGrupoAtletaCreacionCompleta(SimpleTestCase):
    """
    Test completo del caso de uso: Crear un grupo de atleta.
    """

    def setUp(self):
        """Configuración inicial para los tests."""
        # Mock transaction.atomic context manager
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        # Setup del factory y view
        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view({"post": "create"})
        
        # Token para Entrenador
        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_atleta_completo_exitoso(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):

        mock_get_persona.return_value = { "first_name": "Test" }

        # Mock del entrenador autenticado
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador.especialidad = "Baloncesto Juvenil"
        mock_entrenador_objects.get.return_value = mock_entrenador

        # Mock de atletas con edades 
        mock_atleta1 = MagicMock(spec=Atleta)
        mock_atleta1.id = 1
        mock_atleta1.edad = 14
        mock_atleta1.persona_external = "atleta-001"

        mock_atleta2 = MagicMock(spec=Atleta)
        mock_atleta2.id = 2
        mock_atleta2.edad = 18
        mock_atleta2.persona_external = "atleta-002"

        # Configurar el filter de atletas para validación
        # Usar side_effect para que el mock responda segun los ids solicitados
        def filter_atletas(**kwargs):
            ids_solicitados = kwargs.get('id__in', [])
            atletas_disponibles = {1: mock_atleta1, 2: mock_atleta2}
            # Solo devolver atletas cuyo ID fue solicitado Y existe
            return [atletas_disponibles[id] for id in ids_solicitados if id in atletas_disponibles]
        
        mock_atleta_objects.filter.side_effect = filter_atletas

        # Mock de verificación de nombre único (no existe)
        mock_grupo_objects.filter.return_value.exists.return_value = False

        # Mock del grupo creado por el DAO
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
        mock_grupo.atletas.set = MagicMock()

        # Usar service REAL con DAO mockeado, para ejecutar las validaciones
        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        # Ejecutar la creación del grupo
        data = {
            "nombre": "Grupo Juvenil A",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1, 2], 
        }

        # Ejecutar la solicitud POST
        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nombre"], "Grupo Juvenil A")
        self.assertEqual(response.data["rango_edad_minima"], 14)
        self.assertEqual(response.data["rango_edad_maxima"], 18)
        self.assertEqual(response.data["categoria"], "Juvenil")

        # Verificar que el DAO fue llamado correctamente
        real_service.dao.create.assert_called_once()
        
        # Verificar que se asignaron los atletas
        mock_grupo.atletas.set.assert_called_once_with([mock_atleta1, mock_atleta2])

class TestGrupoAtletaBajaCompleta(SimpleTestCase):
    """
    Test completo del caso de uso: Dar de baja un grupo de atleta.    
    """

    def setUp(self):
        """Configuración inicial para los tests."""
        # Mock transaction.atomic context manager
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view({"delete": "destroy"})
        
        # Token para Entrenador
        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_dar_baja_grupo_atleta_completo_exitoso(self, mock_entrenador_objects):
        
        # Mock del entrenador autenticado
        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        # Mock del grupo a eliminar
        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1 
        mock_grupo.nombre = "Grupo a Eliminar"
        mock_grupo.entrenador_id = 1
        mock_grupo.eliminado = False

        # Usar service REAL con DAO mockeado, para ejecutar las validaciones
        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        
        # Configurar el mock para que solo devuelva el grupo si el ID coincide.
        def get_by_id_side_effect(id_pedido):
            if int(id_pedido) == mock_grupo.id:
                return mock_grupo
            return None
            
        real_service.dao.get_by_id_activo.side_effect = get_by_id_side_effect
        real_service.dao.update.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        # Ejecutar la baja del grupo
        request = self.factory.delete(
            "/api/grupos-atletas/1/", HTTP_AUTHORIZATION=self.auth_header
        )
        response = self.view(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar que el DAO fue llamado correctamente
        real_service.dao.get_by_id_activo.assert_called_once_with(1)