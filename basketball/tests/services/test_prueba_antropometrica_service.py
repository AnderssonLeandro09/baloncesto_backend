"""Pruebas unitarias para PruebaAntropometricaService."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from django.test import TestCase

from ...models import Atleta, Sexo, Entrenador
from ...services.prueba_antropometrica_service import PruebaAntropometricaService


class PruebaAntropometricaServiceTest(TestCase):
    def setUp(self):
        self.service = PruebaAntropometricaService()
        self.atleta = Atleta.objects.create(
            persona_external="uuid-maria-lopez",
            fecha_nacimiento=date(2012, 5, 20),
            edad=13,
            sexo=Sexo.FEMENINO,
        )
        self.entrenador = Entrenador.objects.create(
            persona_external="uuid-entrenador",
            especialidad="Baloncesto",
            club_asignado="Club Test",
        )
        self.user = MagicMock()
        self.user.entrenador = self.entrenador

    def test_create_prueba_antropometrica_service(self):
        data = {
            "atleta_id": self.atleta.id,
            "fecha_registro": date.today(),
            "peso": Decimal('48.5'),
            "estatura": Decimal('1.55'),
            "altura_sentado": Decimal('0.82'),
            "envergadura": Decimal('1.60'),
            "observaciones": "Medición inicial",
        }

        prueba = self.service.create_prueba_antropometrica(data, self.user)

        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta.id, self.atleta.id)
        self.assertEqual(float(prueba.peso), 48.5)

    def test_get_pruebas_by_atleta_service(self):
        data = {
            "atleta_id": self.atleta.id,
            "fecha_registro": date.today(),
            "peso": Decimal('47.0'),
            "estatura": Decimal('1.54'),
            "altura_sentado": Decimal('0.81'),
            "envergadura": Decimal('1.59'),
        }

        self.service.create_prueba_antropometrica(data, self.user)

        pruebas = self.service.get_pruebas_by_atleta(self.atleta.id)

        self.assertEqual(len(pruebas), 1)
        self.assertEqual(pruebas[0].atleta.id, self.atleta.id)
