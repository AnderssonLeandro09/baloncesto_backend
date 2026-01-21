"""
Tests completos para la creación de Grupos de Atletas usando mocks.

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


class TestGrupoAtletaCreacion(SimpleTestCase):
    """Tests para la creación de grupos de atletas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = GrupoAtletaController.as_view({"post": "create"})

        payload = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.auth_header = f"Bearer {self.token}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de creación exitosa
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_atleta_completo_exitoso(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Crear un grupo de atletas con todos los datos válidos."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador.especialidad = "Baloncesto Juvenil"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta1 = MagicMock(spec=Atleta)
        mock_atleta1.id = 1
        mock_atleta1.edad = 14
        mock_atleta1.persona_external = "atleta-001"

        mock_atleta2 = MagicMock(spec=Atleta)
        mock_atleta2.id = 2
        mock_atleta2.edad = 18
        mock_atleta2.persona_external = "atleta-002"

        # Mock para Atleta.objects.filter() - usado tanto en serializer como en service
        atletas_map = {1: mock_atleta1, 2: mock_atleta2}
        
        def atleta_filter_mock(**kwargs):
            if 'id' in kwargs:
                # Para el serializer - retorna un QuerySet mock con .first()
                atleta_id = kwargs['id']
                mock_filter_result = MagicMock()
                mock_filter_result.first.return_value = atletas_map.get(atleta_id)
                return mock_filter_result
            elif 'id__in' in kwargs:
                # Para el service - retorna un QuerySet mock iterable
                ids = kwargs['id__in']
                filtered_atletas = [atletas_map[aid] for aid in ids if aid in atletas_map]
                mock_queryset = MagicMock()
                mock_queryset.__iter__.return_value = iter(filtered_atletas)
                mock_queryset.__len__.return_value = len(filtered_atletas)
                mock_queryset.count.return_value = len(filtered_atletas)
                return mock_queryset
            return MagicMock()
        
        mock_atleta_objects.filter.side_effect = atleta_filter_mock
        mock_grupo_objects.filter.return_value.exists.return_value = False

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

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Juvenil A",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1, 2],
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["nombre"], "Grupo Juvenil A")
        self.assertEqual(response.data["data"]["rango_edad_minima"], 14)
        self.assertEqual(response.data["data"]["rango_edad_maxima"], 18)
        self.assertEqual(response.data["data"]["categoria"], "Juvenil")
        real_service.dao.create.assert_called_once()
        mock_grupo.atletas.set.assert_called_once()  # Verificar que se llamó

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_sin_atletas_exitoso(
        self,
        mock_entrenador_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Crear un grupo de atletas sin asignar atletas inicialmente."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo_objects.filter.return_value.exists.return_value = False

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Infantil B"
        mock_grupo.rango_edad_minima = 10
        mock_grupo.rango_edad_maxima = 14
        mock_grupo.categoria = "Infantil Base"
        mock_grupo.estado = True
        mock_grupo.eliminado = False
        mock_grupo.entrenador_id = 1
        mock_grupo.atletas.all.return_value = []

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Infantil B",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 14,
            "categoria": "Infantil Base",
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["nombre"], "Grupo Infantil B")
        real_service.dao.create.assert_called_once()

    # =========================================================================
    # Tests de atletas fuera del rango de edad
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_atleta_con_edad_menor_al_rango(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando un atleta tiene edad menor al rango mínimo del grupo."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta_menor = MagicMock(spec=Atleta)
        mock_atleta_menor.id = 1
        mock_atleta_menor.edad = 10  # Menor que el rango mínimo de 14

        # Mock para Atleta.objects.filter() - usado tanto en serializer como en service
        atletas_map = {1: mock_atleta_menor}
        
        def atleta_filter_mock(**kwargs):
            if 'id' in kwargs:
                atleta_id = kwargs['id']
                mock_filter_result = MagicMock()
                mock_filter_result.first.return_value = atletas_map.get(atleta_id)
                return mock_filter_result
            elif 'id__in' in kwargs:
                ids = kwargs['id__in']
                filtered_atletas = [atletas_map[aid] for aid in ids if aid in atletas_map]
                mock_queryset = MagicMock()
                mock_queryset.__iter__.return_value = iter(filtered_atletas)
                mock_queryset.__len__.return_value = len(filtered_atletas)
                mock_queryset.count.return_value = len(filtered_atletas)
                return mock_queryset
            return MagicMock()
        
        mock_atleta_objects.filter.side_effect = atleta_filter_mock
        mock_grupo_objects.filter.return_value.exists.return_value = False

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Juvenil"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.atletas.set = MagicMock()

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Juvenil",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1],
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        # La validación del serializer pone los errores en data
        self.assertIn("atletas", str(response.data["data"]).lower())
        self.assertIn("rango", str(response.data["data"]).lower())

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_atleta_con_edad_mayor_al_rango(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando un atleta tiene edad mayor al rango máximo del grupo."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta_mayor = MagicMock(spec=Atleta)
        mock_atleta_mayor.id = 1
        mock_atleta_mayor.edad = 25  # Mayor que el rango máximo de 18

        # Mock para Atleta.objects.filter() - usado tanto en serializer como en service
        atletas_map = {1: mock_atleta_mayor}
        
        def atleta_filter_mock(**kwargs):
            if 'id' in kwargs:
                atleta_id = kwargs['id']
                mock_filter_result = MagicMock()
                mock_filter_result.first.return_value = atletas_map.get(atleta_id)
                return mock_filter_result
            elif 'id__in' in kwargs:
                ids = kwargs['id__in']
                filtered_atletas = [atletas_map[aid] for aid in ids if aid in atletas_map]
                mock_queryset = MagicMock()
                mock_queryset.__iter__.return_value = iter(filtered_atletas)
                mock_queryset.__len__.return_value = len(filtered_atletas)
                mock_queryset.count.return_value = len(filtered_atletas)
                return mock_queryset
            return MagicMock()
        
        mock_atleta_objects.filter.side_effect = atleta_filter_mock
        mock_grupo_objects.filter.return_value.exists.return_value = False

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Juvenil"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.atletas.set = MagicMock()

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Juvenil",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1],
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        # La validación del serializer pone los errores en data
        self.assertIn("atletas", str(response.data["data"]).lower())
        self.assertIn("rango", str(response.data["data"]).lower())

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_atleta_con_mezcla_edades_validas_e_invalidas(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando hay atletas con edades válidas e inválidas mezclados."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta_valido = MagicMock(spec=Atleta)
        mock_atleta_valido.id = 1
        mock_atleta_valido.edad = 16

        mock_atleta_invalido = MagicMock(spec=Atleta)
        mock_atleta_invalido.id = 2
        mock_atleta_invalido.edad = 25

        # Mock para Atleta.objects.filter() - usado tanto en serializer como en service
        atletas_map = {1: mock_atleta_valido, 2: mock_atleta_invalido}
        
        def atleta_filter_mock(**kwargs):
            if 'id' in kwargs:
                atleta_id = kwargs['id']
                mock_filter_result = MagicMock()
                mock_filter_result.first.return_value = atletas_map.get(atleta_id)
                return mock_filter_result
            elif 'id__in' in kwargs:
                ids = kwargs['id__in']
                filtered_atletas = [atletas_map[aid] for aid in ids if aid in atletas_map]
                mock_queryset = MagicMock()
                mock_queryset.__iter__.return_value = iter(filtered_atletas)
                mock_queryset.__len__.return_value = len(filtered_atletas)
                mock_queryset.count.return_value = len(filtered_atletas)
                return mock_queryset
            return MagicMock()
        
        mock_atleta_objects.filter.side_effect = atleta_filter_mock
        mock_grupo_objects.filter.return_value.exists.return_value = False

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Juvenil"
        mock_grupo.rango_edad_minima = 14
        mock_grupo.rango_edad_maxima = 18
        mock_grupo.categoria = "Juvenil"
        mock_grupo.atletas.set = MagicMock()

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Juvenil",
            "rango_edad_minima": 14,
            "rango_edad_maxima": 18,
            "categoria": "Juvenil",
            "atletas": [1, 2],
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")

    # =========================================================================
    # Tests de nombre duplicado
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_con_nombre_duplicado_falla(
        self,
        mock_entrenador_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando ya existe un grupo con el mismo nombre."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_grupo_objects.filter.return_value.exists.return_value = (
            True  # Ya existe el nombre
        )

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Existente",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 15,
            "categoria": "Infantil Base",
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        # El error de validación del serializer va en data
        self.assertIn("nombre", str(response.data["data"]).lower())
        self.assertIn("ya existe", str(response.data["data"]).lower())

    # =========================================================================
    # Tests de atletas inexistentes
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.models.Atleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_crear_grupo_con_atletas_inexistentes_falla(
        self,
        mock_entrenador_objects,
        mock_atleta_objects,
        mock_grupo_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando se intenta asignar atletas que no existen."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.get.return_value = mock_entrenador

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.edad = 15

        # Solo existe el atleta 1, no el 999
        atletas_map = {1: mock_atleta}
        
        def atleta_filter_mock(**kwargs):
            if 'id' in kwargs:
                atleta_id = kwargs['id']
                mock_filter_result = MagicMock()
                mock_filter_result.first.return_value = atletas_map.get(atleta_id)
                return mock_filter_result
            elif 'id__in' in kwargs:
                ids = kwargs['id__in']
                filtered_atletas = [atletas_map[aid] for aid in ids if aid in atletas_map]
                mock_queryset = MagicMock()
                mock_queryset.__iter__.return_value = iter(filtered_atletas)
                mock_queryset.__len__.return_value = len(filtered_atletas)
                mock_queryset.count.return_value = len(filtered_atletas)
                return mock_queryset
            return MagicMock()
        
        mock_atleta_objects.filter.side_effect = atleta_filter_mock
        mock_grupo_objects.filter.return_value.exists.return_value = False

        mock_grupo = MagicMock(spec=GrupoAtleta)
        mock_grupo.id = 1
        mock_grupo.nombre = "Grupo Test"
        mock_grupo.rango_edad_minima = 10
        mock_grupo.rango_edad_maxima = 20
        mock_grupo.categoria = "Categoria Test"

        real_service = GrupoAtletaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_grupo
        GrupoAtletaController.service = real_service

        data = {
            "nombre": "Grupo Test",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 20,
            "categoria": "Categoria Test",
            "atletas": [1, 999],  # 999 no existe
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "error")
        # La validación del serializer pone los errores en data
        self.assertIn("atleta", str(response.data["data"]).lower())
        self.assertIn("no existe", str(response.data["data"]).lower())

    # =========================================================================
    # Tests sin autenticación
    # =========================================================================

    def test_crear_grupo_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        data = {
            "nombre": "Grupo Test",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 20,
            "categoria": "Categoria Test",
        }

        request = self.factory.post(
            "/api/grupos-atletas/",
            data=data,
            format="json",
        )
        response = self.view(request)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
