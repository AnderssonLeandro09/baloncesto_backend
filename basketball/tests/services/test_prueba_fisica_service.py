"""Pruebas unitarias para PruebaFisicaService."""

from django.test import TestCase
from ...models import Atleta, TipoPrueba, Sexo
from ...services.prueba_fisica_service import PruebaFisicaService
from datetime import date


class PruebaFisicaServiceTest(TestCase):
    def setUp(self):
        self.service = PruebaFisicaService()
        self.atleta = Atleta.objects.create(
            persona_external="uuid-maria-lopez",
            fecha_nacimiento=date(2012, 5, 20),
            edad=13,
            sexo=Sexo.FEMENINO,
        )

    def test_create_prueba_fisica_service(self):
        data = {
            "atleta_id": self.atleta.id,
            "fecha_registro": date.today(),
            "tipo_prueba": TipoPrueba.FUERZA,
            "resultado": 40.0,
            "unidad_medida": "kg",
            "observaciones": "Test service",
        }
        prueba = self.service.create_prueba_fisica(data)
        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta.id, self.atleta.id)

    def test_get_pruebas_by_atleta_service(self):
        data = {
            "atleta_id": self.atleta.id,
            "fecha_registro": date.today(),
            "tipo_prueba": TipoPrueba.VELOCIDAD,
            "resultado": 11.0,
            "unidad_medida": "s",
        }
        self.service.create_prueba_fisica(data)
        pruebas = self.service.get_pruebas_by_atleta(self.atleta.id)
        self.assertEqual(len(pruebas), 1)
        self.assertEqual(pruebas[0].tipo_prueba, TipoPrueba.VELOCIDAD)
