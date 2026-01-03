"""Pruebas unitarias para PruebaAntropometricaDAO."""

from datetime import date
from django.test import TestCase

from ...models import (
    Atleta,
    Sexo,
)
from ...dao.prueba_antropometrica_dao import PruebaAntropometricaDAO


class PruebaAntropometricaDAOTest(TestCase):
    def setUp(self):
        self.dao = PruebaAntropometricaDAO()
        self.atleta = Atleta.objects.create(
            persona_external="uuid-juan-perez",
            fecha_nacimiento=date(2010, 1, 1),
            edad=15,
            sexo=Sexo.MASCULINO,
        )

    def test_create_prueba_antropometrica(self):
        prueba = self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            peso=70.5,
            estatura=1.75,
            altura_sentado=0.90,
            envergadura=1.80,
            observaciones="Medición inicial",
        )

        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta, self.atleta)
        self.assertEqual(float(prueba.peso), 70.5)
        self.assertEqual(float(prueba.estatura), 1.75)

    def test_get_by_atleta(self):
        self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            peso=68.0,
            estatura=1.72,
            altura_sentado=0.88,
            envergadura=1.78,
        )

        pruebas = self.dao.get_by_atleta(self.atleta.id)
        self.assertEqual(pruebas.count(), 1)
        self.assertEqual(pruebas[0].atleta, self.atleta)

    def test_update_prueba_antropometrica(self):
        prueba = self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            peso=72.0,
            estatura=1.76,
            altura_sentado=0.91,
            envergadura=1.82,
        )

        updated = self.dao.update(prueba.id, peso=71.3)

        self.assertEqual(float(updated.peso), 71.3)
