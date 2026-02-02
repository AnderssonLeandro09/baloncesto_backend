from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
import jwt
from django.conf import settings
from datetime import date, timedelta
from decimal import Decimal

from basketball.controllers.prueba_fisica_controller import PruebaFisicaController
from basketball.services.prueba_fisica_service import PruebaFisicaService
from basketball.models import PruebaFisica, Atleta, Entrenador, Inscripcion


class TestPruebaFisicaCreacion(SimpleTestCase):
    """Tests para la creación de pruebas físicas."""

    def setUp(self):
        """Configuración inicial para los tests."""
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.factory = APIRequestFactory()
        self.view = PruebaFisicaController.as_view({"post": "create"})

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
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_crear_prueba_fisica_fuerza_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Crear una prueba física de fuerza con todos los datos válidos."""
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

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.atleta = mock_atleta
        mock_prueba.fecha_registro = date.today()
        mock_prueba.tipo_prueba = "FUERZA"
        mock_prueba.resultado = Decimal("150.50")
        mock_prueba.unidad_medida = "Centímetros (cm)"
        mock_prueba.observaciones = "Buen salto horizontal"
        mock_prueba.estado = True

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
            "observaciones": "Buen salto horizontal",
            "estado": True,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_prueba
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.50",
            "observaciones": "Buen salto horizontal",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        real_service.dao.create.assert_called_once()

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_crear_prueba_fisica_velocidad_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Crear una prueba física de velocidad con datos válidos."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_inscripcion = MagicMock(spec=Inscripcion)
        mock_inscripcion.habilitada = True

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 2
        mock_atleta.persona_external = "atleta-002"
        mock_atleta.inscripcion = mock_inscripcion
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 2
        mock_prueba.atleta = mock_atleta
        mock_prueba.fecha_registro = date.today()
        mock_prueba.tipo_prueba = "VELOCIDAD"
        mock_prueba.resultado = Decimal("5.45")
        mock_prueba.unidad_medida = "Segundos (seg)"
        mock_prueba.observaciones = "Buena velocidad en 30m"
        mock_prueba.estado = True

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
            "observaciones": "Buena velocidad en 30m",
            "estado": True,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_prueba
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 2,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "VELOCIDAD",
            "resultado": "5.45",
            "observaciones": "Buena velocidad en 30m",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        real_service.dao.create.assert_called_once()

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    @patch.object(PruebaFisicaService, "get_prueba_fisica_completa")
    def test_crear_prueba_fisica_agilidad_exitoso(
        self,
        mock_get_prueba_completa,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Crear una prueba física de agilidad (zigzag) con datos válidos."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_inscripcion = MagicMock(spec=Inscripcion)
        mock_inscripcion.habilitada = True

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 3
        mock_atleta.persona_external = "atleta-003"
        mock_atleta.inscripcion = mock_inscripcion
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 3
        mock_prueba.atleta = mock_atleta
        mock_prueba.fecha_registro = date.today()
        mock_prueba.tipo_prueba = "AGILIDAD"
        mock_prueba.resultado = Decimal("12.30")
        mock_prueba.unidad_medida = "Segundos (seg)"
        mock_prueba.observaciones = "Prueba de zigzag"
        mock_prueba.estado = True

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
            "observaciones": "Prueba de zigzag",
            "estado": True,
            "semestre": "2026-1",
        }

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.dao.create.return_value = mock_prueba
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        real_service.get_prueba_fisica_completa = mock_get_prueba_completa
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 3,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "AGILIDAD",
            "resultado": "12.30",
            "observaciones": "Prueba de zigzag",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        real_service.dao.create.assert_called_once()

    # =========================================================================
    # Tests de validación de atleta
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_atleta_inexistente_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el atleta no existe."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = None  # Atleta no existe
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 999,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("El atleta con ID 999 no existe", response.data["error"])

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_atleta_sin_inscripcion_habilitada_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el atleta no tiene inscripción habilitada."""
        mock_get_persona.return_value = {"first_name": "Test"}

        mock_entrenador = MagicMock(spec=Entrenador)
        mock_entrenador.id = 1
        mock_entrenador.persona_external = "entrenador-123"
        mock_entrenador_objects.filter.return_value.first.return_value = mock_entrenador

        mock_inscripcion = MagicMock(spec=Inscripcion)
        mock_inscripcion.habilitada = False  # Inscripción NO habilitada

        mock_atleta = MagicMock(spec=Atleta)
        mock_atleta.id = 1
        mock_atleta.persona_external = "atleta-001"
        mock_atleta.inscripcion = mock_inscripcion
        mock_atleta.grupos.filter.return_value.exists.return_value = True

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn(
            '"El atleta no tiene inscripción habilitada". No se guarda el registro.',
            response.data["error"],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_sin_atleta_id_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando no se proporciona el ID del atleta."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_atleta_id_invalido_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el ID del atleta no es un número válido."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": "abc",
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_atleta_id_negativo_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el ID del atleta es negativo."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": -1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Tests de validación de fecha
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_fecha_futura_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando la fecha de registro es futura."""
        mock_get_persona.return_value = {"first_name": "Test"}

        fecha_futura = date.today() + timedelta(days=10)
        data = {
            "atleta_id": 1,
            "fecha_registro": str(fecha_futura),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_registro", response.data)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_sin_fecha_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando no se proporciona la fecha de registro."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Tests de validación de tipo de prueba
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_tipo_invalido_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el tipo de prueba no es válido."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "TIPO_INVALIDO",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tipo_prueba", response.data)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_sin_tipo_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando no se proporciona el tipo de prueba."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # Tests de validación de resultado
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_resultado_negativo_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el resultado es negativo."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "-10.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_resultado_cero_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando el resultado es cero."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "0.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("basketball.serializers.get_persona_from_user_module")
    def test_crear_prueba_fisica_sin_resultado_falla(
        self,
        mock_get_persona,
    ):
        """Test: Falla cuando no se proporciona el resultado."""
        mock_get_persona.return_value = {"first_name": "Test"}

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_resultado_excede_rango_fuerza_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el resultado de fuerza excede el rango máximo (300 cm)."""
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

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "350.00",  # Excede el máximo de 300 para FUERZA
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn(
            "El resultado excede el rango máximo para FUERZA: 300",
            response.data["error"],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_resultado_excede_rango_velocidad_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el resultado de velocidad excede el rango máximo (15 seg)."""
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

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "VELOCIDAD",
            "resultado": "20.00",  # Excede el máximo de 15 para VELOCIDAD
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn(
            "El resultado excede el rango máximo para VELOCIDAD: 15",
            response.data["error"],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_resultado_excede_rango_agilidad_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el resultado de agilidad excede el rango máximo (25 seg)."""
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

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "AGILIDAD",
            "resultado": "30.00",  # Excede el máximo de 25 para AGILIDAD
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn(
            "El resultado excede el rango máximo para AGILIDAD: 25",
            response.data["error"],
        )

    # =========================================================================
    # Tests de validación de observaciones
    # =========================================================================

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_observaciones_exceden_limite_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando las observaciones exceden 200 caracteres."""
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

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        observaciones_largas = "A" * 250  # 250 caracteres, excede el límite de 200
        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
            "observaciones": observaciones_largas,
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn(
            "Las observaciones no pueden exceder 200 caracteres",
            response.data["error"],
        )

    # =========================================================================
    # Tests de autenticación y permisos
    # =========================================================================

    def test_crear_prueba_fisica_sin_token_falla(self):
        """Test: Falla cuando no se proporciona token de autenticación."""
        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
        )
        response = self.view(request)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("basketball.serializers.get_persona_from_user_module")
    @patch("basketball.services.prueba_fisica_service.Entrenador.objects")
    def test_crear_prueba_fisica_entrenador_sin_permiso_atleta_falla(
        self,
        mock_entrenador_objects,
        mock_get_persona,
    ):
        """Test: Falla cuando el entrenador no tiene permiso sobre el atleta."""
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
        # El atleta NO pertenece a los grupos del entrenador
        mock_atleta.grupos.filter.return_value.exists.return_value = False

        real_service = PruebaFisicaService()
        real_service.dao = MagicMock()
        real_service.atleta_dao = MagicMock()
        real_service.atleta_dao.get_by_id.return_value = mock_atleta
        PruebaFisicaController.service = real_service

        data = {
            "atleta_id": 1,
            "fecha_registro": str(date.today()),
            "tipo_prueba": "FUERZA",
            "resultado": "150.00",
        }

        request = self.factory.post(
            "/api/pruebas-fisicas/",
            data=data,
            format="json",
            HTTP_AUTHORIZATION=self.auth_header,
        )
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
        self.assertIn(
            "No tiene permiso para registrar pruebas a este atleta",
            response.data["error"],
        )
