"""Tests del servicio de Inscripcion usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import date

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.inscripcion_service import InscripcionService


class InscripcionServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = InscripcionService()
        self.service.atleta_dao = MagicMock()
        self.service.inscripcion_dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(
            return_value={"data": {"first_name": "Juan", "last_name": "Perez"}}
        )

    def test_create_requires_persona(self):
        with self.assertRaises(ValidationError):
            self.service.create_atleta_inscripcion({}, {}, {}, "token")

    def test_create_requires_email_password(self):
        # Missing email
        with self.assertRaises(ValidationError):
            self.service.create_atleta_inscripcion(
                {"first_name": "Juan", "password": "pwd"},
                {},
                {},
                "token",
            )
        # Missing password
        with self.assertRaises(ValidationError):
            self.service.create_atleta_inscripcion(
                {"first_name": "Juan", "email": "juan@test.com"},
                {},
                {},
                "token",
            )

    def test_create_atleta_inscripcion_success(self):
        # Mock save-account response
        self.service._call_user_module.side_effect = [
            {"data": {}},  # save-account response
            {"data": {"external": "atleta-uuid"}},  # search response
        ]

        self.service.atleta_dao.exists.return_value = False

        atleta_obj = SimpleNamespace(
            id=1,
            persona_external="atleta-uuid",
            fecha_nacimiento=None,
            edad=15,
            sexo="MASCULINO",
            telefono="0999999996",
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
        )
        self.service.atleta_dao.create.return_value = atleta_obj

        inscripcion_obj = SimpleNamespace(
            id=1,
            atleta=atleta_obj,
            fecha_inscripcion=date.today(),
            tipo_inscripcion="ORDINARIA",
            fecha_creacion=date.today(),
            habilitada=True,
        )
        self.service.inscripcion_dao.get_by_filter.return_value.first.return_value = (
            None
        )
        self.service.inscripcion_dao.create.return_value = inscripcion_obj

        result = self.service.create_atleta_inscripcion(
            {
                "first_name": "Juan",
                "identification": "0102030406",
                "email": "juan@test.com",
                "password": "pass",
            },
            {
                "edad": 15,
                "sexo": "MASCULINO",
            },
            {},
            "token",
        )

        self.assertEqual(result["atleta"]["persona_external"], "atleta-uuid")
        self.assertEqual(result["inscripcion"]["habilitada"], True)
        self.service.atleta_dao.create.assert_called()
        self.service.inscripcion_dao.create.assert_called()

    def test_cambiar_estado_inscripcion_success(self):
        inscripcion_obj = SimpleNamespace(id=1, habilitada=True)
        self.service.inscripcion_dao.get_by_id.return_value = inscripcion_obj
        self.service.inscripcion_dao.update.return_value = SimpleNamespace(
            id=1, habilitada=False
        )

        result = self.service.cambiar_estado_inscripcion(1)
        self.assertFalse(result.habilitada)
        self.service.inscripcion_dao.update.assert_called_with(1, habilitada=False)
