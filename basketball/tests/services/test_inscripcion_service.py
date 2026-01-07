"""Tests del servicio de Inscripcion usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import date

# Para el servicio usamos la excepción de Django ya que es lógica de negocio pura
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.inscripcion_service import InscripcionService


class InscripcionServiceTests(SimpleTestCase):
    def setUp(self):
        # Inicialización del servicio con mocks para evitar acceso a DB y red
        self.service = InscripcionService()
        self.service.atleta_dao = MagicMock()
        self.service.inscripcion_dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(
            return_value={"data": {"first_name": "Juan", "last_name": "Perez"}}
        )

    def test_create_requires_persona(self):
        """Verifica que se lance ValidationError si faltan datos de persona."""
        with self.assertRaises(ValidationError):
            self.service.create_atleta_inscripcion({}, {}, {}, "token")

    def test_create_generates_dummy_credentials(self):
        """
        MODO FAIL-SAFE: Verifica que el servicio genere credenciales dummy si no se proporcionan,
        permitiendo que el flujo continúe sin errores de validación por email/password.
        """
        # Configuración de mocks para simular que no existe el atleta ni la inscripción
        self.service._call_user_module.return_value = {
            "data": {"external": "test-uuid"}
        }
        self.service.atleta_dao.get_by_filter.return_value.first.return_value = None
        self.service.atleta_dao.exists.return_value = False

        # Simulamos un objeto Atleta creado exitosamente
        atleta_obj = SimpleNamespace(
            id=1,
            persona_external="test-uuid",
            nombres="Juan",
            apellidos="Perez",
            cedula="0102030405",
            fecha_nacimiento=None,
            edad=15,
            sexo="MASCULINO",
            telefono="0999999996",
            tipo_sangre="O+",
            alergias="Ninguna",
            enfermedades="Ninguna",
            medicamentos="Ninguno",
            lesiones="Ninguna",
            nombre_representante="Pedro",
            cedula_representante="0102030407",
            parentesco_representante="PADRE",
            telefono_representante="0999999997",
            correo_representante="test@test.com",
            direccion_representante="Calle 123",
            ocupacion_representante="Ing",
            email=None,
            direccion=None,
            genero=None,
        )
        self.service.atleta_dao.create.return_value = atleta_obj
        self.service.atleta_dao.get_by_id.return_value = atleta_obj

        # Simulamos la creación de la inscripción
        inscripcion_obj = SimpleNamespace(
            id=1,
            atleta=atleta_obj,
            fecha_inscripcion=date.today(),
            tipo_inscripcion="MAYOR_EDAD",
            fecha_creacion=date.today(),
            habilitada=True,
        )
        self.service.inscripcion_dao.create.return_value = inscripcion_obj

        # Ejecutamos con datos mínimos (sin email ni password)
        result = self.service.create_atleta_inscripcion(
            {"first_name": "Juan", "identification": "0102030405"},
            {"edad": 15, "sexo": "MASCULINO"},
            {},
            "token",
        )

        # Verificaciones
        self.assertIn("atleta", result)
        self.assertIn("inscripcion", result)
        self.assertEqual(result["atleta"]["persona_external"], "test-uuid")

    def test_create_atleta_inscripcion_success(self):
        """Prueba de flujo completo exitoso con credenciales proporcionadas."""
        self.service._call_user_module.return_value = {
            "data": {"external": "atleta-uuid"}
        }

        self.service.atleta_dao.exists.return_value = False
        self.service.atleta_dao.get_by_filter.return_value.first.return_value = None

        atleta_obj = SimpleNamespace(
            id=1,
            persona_external="atleta-uuid",
            nombres="Juan",
            apellidos="Perez",
            cedula="0102030406",
            email="juan@test.com",
            telefono="0999999999",
            fecha_nacimiento=date(2010, 1, 1),
            edad=15,
            sexo="MASCULINO",
            tipo_sangre="O+",
            alergias="Ninguna",
            enfermedades="Ninguna",
            medicamentos="Ninguno",
            lesiones="Ninguna",
            nombre_representante="Pedro Perez",
            cedula_representante="0102030407",
            parentesco_representante="PADRE",
            telefono_representante="0999999997",
            correo_representante="pedro.perez@test.com",
            direccion_representante="Calle Falsa 123",
            ocupacion_representante="Ingeniero",
            direccion="Cuenca",
            genero="MASCULINO"
        )
        self.service.atleta_dao.create.return_value = atleta_obj
        self.service.atleta_dao.get_by_id.return_value = atleta_obj

        inscripcion_obj = SimpleNamespace(
            id=1,
            atleta=atleta_obj,
            fecha_inscripcion=date.today(),
            fecha_creacion=date.today(),
            tipo_inscripcion="MAYOR_EDAD",
            habilitada=True,
        )
        self.service.inscripcion_dao.get_by_filter.return_value.first.return_value = None
        self.service.inscripcion_dao.create.return_value = inscripcion_obj

        result = self.service.create_atleta_inscripcion(
            {
                "first_name": "Juan",
                "identification": "0102030406",
                "email": "juan@test.com",
                "password": "pass",
            },
            {"edad": 15, "sexo": "MASCULINO"},
            {},
            "token",
        )

        self.assertEqual(result["atleta"]["persona_external"], "atleta-uuid")
        self.assertTrue(result["inscripcion"]["habilitada"])

    def test_cambiar_estado_inscripcion_success(self):
        """Verifica que el cambio de estado (toggle) funcione a través del DAO."""
        inscripcion_obj = SimpleNamespace(id=1, habilitada=True)
        self.service.inscripcion_dao.get_by_id.return_value = inscripcion_obj
        self.service.inscripcion_dao.update.return_value = SimpleNamespace(
            id=1, habilitada=False
        )

        result = self.service.cambiar_estado_inscripcion(1)
        self.assertFalse(result.habilitada)
        self.service.inscripcion_dao.update.assert_called_with(1, habilitada=False)
