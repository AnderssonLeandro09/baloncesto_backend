from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings
from datetime import date
from decimal import Decimal

from basketball.controllers.prueba_fisica_controller import PruebaFisicaController
from basketball.services.prueba_fisica_service import PruebaFisicaService
from basketball.models import PruebaFisica, Atleta, Entrenador, Inscripcion


class TestDesactivarPruebaFisica(SimpleTestCase):
    """Tests para la desactivación (toggle estado) de pruebas físicas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = PruebaFisicaController.as_view({"patch": "toggle_estado"})

        # Token de ENTRENADOR
        payload_entrenador = {"role": "ENTRENADOR", "sub": "entrenador-123"}
        self.token_entrenador = jwt.encode(
            payload_entrenador, settings.SECRET_KEY, algorithm="HS256"
        )
        self.auth_header_entrenador = f"Bearer {self.token_entrenador}"

        # Token de ESTUDIANTE_VINCULACION
        payload_estudiante = {"role": "ESTUDIANTE_VINCULACION", "sub": "estudiante-456"}
        self.token_estudiante = jwt.encode(
            payload_estudiante, settings.SECRET_KEY, algorithm="HS256"
        )
        self.auth_header_estudiante = f"Bearer {self.token_estudiante}"

    def tearDown(self):
        """Limpieza después de cada test."""
        patch.stopall()

    # =========================================================================
    # Tests de desactivación exitosa
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_desactivar_prueba_fisica_activa_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Desactivar una prueba física activa exitosamente (estado True -> False)."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_inscripcion = MagicMock(spec=Inscripcion)
        mock_inscripcion.habilitada = True

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.persona_external = "atleta-001"
        mock_atleta.inscripcion = mock_inscripcion
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        mock_prueba_activa = MagicMock(spec=PruebaFisica)
        mock_prueba_activa.id = 1
        mock_prueba_activa.atleta = mock_atleta
        mock_prueba_activa.fecha_registro = date.today()
        mock_prueba_activa.tipo_prueba = "FUERZA"
        mock_prueba_activa.resultado = Decimal("150.50")
        mock_prueba_activa.unidad_medida = "Centímetros (cm)"
        mock_prueba_activa.observaciones = "Buen salto"
        mock_prueba_activa.estado = True  # Activa inicialmente

        mock_prueba_desactivada = MagicMock(spec=PruebaFisica)
        mock_prueba_desactivada.id = 1
        mock_prueba_desactivada.atleta = mock_atleta
        mock_prueba_desactivada.fecha_registro = date.today()
        mock_prueba_desactivada.tipo_prueba = "FUERZA"
        mock_prueba_desactivada.resultado = Decimal("150.50")
        mock_prueba_desactivada.unidad_medida = "Centímetros (cm)"
        mock_prueba_desactivada.observaciones = "Buen salto"
        mock_prueba_desactivada.estado = False  # Desactivada después del toggle

        mock_get_prueba_completa.return_value = {
            "id": 1,
            "atleta": 1,
            "persona": {
                "nombre": "Juan",
                "apellido": "Pérez",
                "identificacion": "1234567890",
            },
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.50",
            "unidad_medida": "Centímetros (cm)",
            "observaciones": "Buen salto",
            "estado": False,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba_activa
        real_service.dao.update.return_value = mock_prueba_desactivada
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        real_service.dao.update.assert_called_once_with(1, estado=False)

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_reactivar_prueba_fisica_inactiva_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Reactivar una prueba física inactiva exitosamente (estado False -> True)."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 2
        mock_atleta.persona_external = "atleta-002"
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        mock_prueba_inactiva = MagicMock(spec=PruebaFisica)
        mock_prueba_inactiva.id = 2
        mock_prueba_inactiva.atleta = mock_atleta
        mock_prueba_inactiva.fecha_registro = date.today()
        mock_prueba_inactiva.tipo_prueba = "VELOCIDAD"
        mock_prueba_inactiva.resultado = Decimal("5.45")
        mock_prueba_inactiva.unidad_medida = "Segundos (seg)"
        mock_prueba_inactiva.observaciones = "Velocidad 30m"
        mock_prueba_inactiva.estado = False  # Inactiva inicialmente

        mock_prueba_activada = MagicMock(spec=PruebaFisica)
        mock_prueba_activada.id = 2
        mock_prueba_activada.atleta = mock_atleta
        mock_prueba_activada.fecha_registro = date.today()
        mock_prueba_activada.tipo_prueba = "VELOCIDAD"
        mock_prueba_activada.resultado = Decimal("5.45")
        mock_prueba_activada.unidad_medida = "Segundos (seg)"
        mock_prueba_activada.observaciones = "Velocidad 30m"
        mock_prueba_activada.estado = True  # Activada después del toggle

        mock_get_prueba_completa.return_value = {
            "id": 2,
            "atleta": 2,
            "persona": {
                "nombre": "María",
                "apellido": "García",
                "identificacion": "0987654321",
            },
            "fecha_registro": str(date.today()),
            "tipo_prueba": "VELOCIDAD",
            "resultado": "5.45",
            "unidad_medida": "Segundos (seg)",
            "observaciones": "Velocidad 30m",
            "estado": True,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba_inactiva
        real_service.dao.update.return_value = mock_prueba_activada
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/2/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        real_service.dao.update.assert_called_once_with(2, estado=True)

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_desactivar_prueba_fisica_como_estudiante_vinculacion_exitoso(
        self,
        mock_get_prueba_completa,
        mock_get_persona,
    ):
        """Test: Estudiante de vinculación puede desactivar pruebas físicas."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 3
        mock_atleta.persona_external = "atleta-003"

        mock_prueba_activa = MagicMock(spec=PruebaFisica)
        mock_prueba_activa.id = 3
        mock_prueba_activa.atleta = mock_atleta
        mock_prueba_activa.fecha_registro = date.today()
        mock_prueba_activa.tipo_prueba = "AGILIDAD"
        mock_prueba_activa.resultado = Decimal("12.30")
        mock_prueba_activa.unidad_medida = "Segundos (seg)"
        mock_prueba_activa.observaciones = "Zigzag"
        mock_prueba_activa.estado = True

        mock_prueba_desactivada = MagicMock(spec=PruebaFisica)
        mock_prueba_desactivada.id = 3
        mock_prueba_desactivada.atleta = mock_atleta
        mock_prueba_desactivada.fecha_registro = date.today()
        mock_prueba_desactivada.tipo_prueba = "AGILIDAD"
        mock_prueba_desactivada.resultado = Decimal("12.30")
        mock_prueba_desactivada.unidad_medida = "Segundos (seg)"
        mock_prueba_desactivada.observaciones = "Zigzag"
        mock_prueba_desactivada.estado = False

        mock_get_prueba_completa.return_value = {
            "id": 3,
            "atleta": 3,
            "persona": {
                "nombre": "Carlos",
                "apellido": "López",
                "identificacion": "1122334455",
            },
            "fecha_registro": str(date.today()),
            "tipo_prueba": "AGILIDAD",
            "resultado": "12.30",
            "unidad_medida": "Segundos (seg)",
            "observaciones": "Zigzag",
            "estado": False,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba_activa
        real_service.dao.update.return_value = mock_prueba_desactivada
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/3/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_estudiante,
        )
        response = self.view(request, pk="3")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        real_service.dao.update.assert_called_once_with(3, estado=False)

    # =========================================================================
    # Tests de validación de ID de prueba
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_desactivar_prueba_fisica_inexistente_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando la prueba física no existe."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = None  # Prueba no existe
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/999/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="999")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Prueba física no encontrada", response.data["error"])

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_desactivar_prueba_fisica_id_invalido_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el ID de la prueba no es un número válido."""
        mock_get_persona.return_value = {"first_name": "Test"}

        request = self.factory.patch(
            "/api/pruebas-fisicas/abc/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="abc")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("ID inválido", response.data["error"])

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_desactivar_prueba_fisica_id_negativo_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el ID de la prueba es negativo."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = (
            None  # No encontrado para IDs negativos
        )
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/-1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="-1")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Tests de autenticación y permisos
    # =========================================================================

    def test_desactivar_prueba_fisica_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
        )
        response = self.view(request, pk="1")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_desactivar_prueba_fisica_entrenador_sin_permiso_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el entrenador no tiene permiso sobre el atleta de la prueba."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.persona_external = "atleta-001"
        # El atleta NO pertenece a los grupos del entrenador
        mock_atleta.grupos.filter.return_value.exists.return_value = False

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.atleta = mock_atleta
        mock_prueba.estado = True

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="1")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        self.assertIn(
            "No tiene permiso para modificar esta prueba", response.data["error"]
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_desactivar_prueba_fisica_entrenador_no_registrado_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el usuario es entrenador pero no está registrado en el sistema."""
        mock_get_persona.return_value = {"first_name": "Test"}

        # No hay entrenador registrado con ese persona_external
        mock_entrenador_objects.filter.return_value.first.return_value = None

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.persona_external = "atleta-001"
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.atleta = mock_atleta
        mock_prueba.estado = True

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response = self.view(request, pk="1")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # Tests con diferentes roles no autorizados
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_desactivar_prueba_fisica_rol_no_autorizado_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el usuario tiene un rol no autorizado (ej: ATLETA)."""
        mock_get_persona.return_value = {"first_name": "Test"}

        # Token con rol no autorizado
        payload_atleta = {"role": "ATLETA", "sub": "atleta-789"}
        token_atleta = jwt.encode(
            payload_atleta, settings.SECRET_KEY, algorithm="HS256"
        )
        auth_header_atleta = f"Bearer {token_atleta}"

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.estado = True

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=auth_header_atleta,
        )
        response = self.view(request, pk="1")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_desactivar_prueba_fisica_rol_administrador_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el usuario es ADMINISTRADOR (solo ENTRENADOR o ESTUDIANTE_VINCULACION pueden)."""
        mock_get_persona.return_value = {"first_name": "Test"}

        # Token con rol de administrador
        payload_admin = {"role": "ADMINISTRADOR", "sub": "admin-001"}
        token_admin = jwt.encode(payload_admin, settings.SECRET_KEY, algorithm="HS256")
        auth_header_admin = f"Bearer {token_admin}"

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.estado = True

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba
        PruebaFisicaController.service = real_service

        request = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=auth_header_admin,
        )
        response = self.view(request, pk="1")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    # =========================================================================
    # Tests de múltiples toggles
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_toggle_estado_multiples_veces_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Toggle de estado múltiples veces funciona correctamente."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.persona_external = "atleta-001"
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        # Primera llamada: True -> False
        mock_prueba_activa = MagicMock(spec=PruebaFisica)
        mock_prueba_activa.id = 1
        mock_prueba_activa.atleta = mock_atleta
        mock_prueba_activa.fecha_registro = date.today()
        mock_prueba_activa.tipo_prueba = "FUERZA"
        mock_prueba_activa.resultado = Decimal("150.00")
        mock_prueba_activa.unidad_medida = "Centímetros (cm)"
        mock_prueba_activa.estado = True

        mock_prueba_desactivada = MagicMock(spec=PruebaFisica)
        mock_prueba_desactivada.id = 1
        mock_prueba_desactivada.atleta = mock_atleta
        mock_prueba_desactivada.fecha_registro = date.today()
        mock_prueba_desactivada.tipo_prueba = "FUERZA"
        mock_prueba_desactivada.resultado = Decimal("150.00")
        mock_prueba_desactivada.unidad_medida = "Centímetros (cm)"
        mock_prueba_desactivada.estado = False

        mock_get_prueba_completa.return_value = {
            "id": 1,
            "atleta": 1,
            "persona": {
                "nombre": "Test",
                "apellido": "Usuario",
                "identificacion": "1234567890",
            },
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
            "unidad_medida": "Centímetros (cm)",
            "estado": False,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.get_by_id.return_value = mock_prueba_activa
        real_service.dao.update.return_value = mock_prueba_desactivada
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        # Primera llamada: desactivar
        request1 = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response1 = self.view(request1, pk="1")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        real_service.dao.update.assert_called_with(1, estado=False)

        # Segunda llamada: reactivar
        real_service.dao.get_by_id.return_value = mock_prueba_desactivada
        mock_prueba_reactivada = MagicMock(spec=PruebaFisica)
        mock_prueba_reactivada.id = 1
        mock_prueba_reactivada.atleta = mock_atleta
        mock_prueba_reactivada.fecha_registro = date.today()
        mock_prueba_reactivada.tipo_prueba = "FUERZA"
        mock_prueba_reactivada.resultado = Decimal("150.00")
        mock_prueba_reactivada.unidad_medida = "Centímetros (cm)"
        mock_prueba_reactivada.estado = True
        real_service.dao.update.return_value = mock_prueba_reactivada

        mock_get_prueba_completa.return_value["estado"] = True

        request2 = self.factory.patch(
            "/api/pruebas-fisicas/1/toggle-estado/",
            format="json",
            HTTP_AUTHORIZATION=self.auth_header_entrenador,
        )
        response2 = self.view(request2, pk="1")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        real_service.dao.update.assert_called_with(1, estado=True)
