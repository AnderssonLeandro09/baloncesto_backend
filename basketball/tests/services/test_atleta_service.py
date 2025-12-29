"""Tests del servicio de Atleta usando mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from datetime import date

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from basketball.services.atleta_service import AtletaService


class AtletaServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = AtletaService()
        self.service.atleta_dao = MagicMock()
        self.service.inscripcion_dao = MagicMock()
        self.service._call_user_module = MagicMock()
        self.service._fetch_persona = MagicMock(
            return_value={"data": {"first_name": "Juan", "last_name": "Perez"}}
        )

    def test_atleta_service_placeholder(self):
        # TODO: Agregar tests específicos de Atleta (ej: pruebas físicas)
        pass
