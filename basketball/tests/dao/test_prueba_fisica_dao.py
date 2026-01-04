"""Pruebas unitarias para PruebaFisicaDAO."""

from django.test import TestCase
from ...models import Atleta, TipoPrueba, Sexo
from ...dao.prueba_fisica_dao import PruebaFisicaDAO
from datetime import date


class PruebaFisicaDAOTest(TestCase):
    def setUp(self):
        self.dao = PruebaFisicaDAO()
        self.atleta = Atleta.objects.create(
            persona_external="uuid-juan-perez",
            fecha_nacimiento=date(2010, 1, 1),
            edad=15,
            sexo=Sexo.MASCULINO,
        )

    def test_create_prueba_fisica(self):
        prueba = self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            tipo_prueba=TipoPrueba.FUERZA,
            resultado=50.5,
            unidad_medida="kg",
            observaciones="Buena fuerza",
        )
        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta, self.atleta)
        self.assertEqual(float(prueba.resultado), 50.5)

    def test_get_by_atleta(self):
        self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            tipo_prueba=TipoPrueba.VELOCIDAD,
            resultado=10.2,
            unidad_medida="s",
        )
        pruebas = self.dao.get_by_atleta(self.atleta.id)
        self.assertEqual(pruebas.count(), 1)
        self.assertEqual(pruebas[0].tipo_prueba, TipoPrueba.VELOCIDAD)

    def test_update_prueba_fisica(self):
        prueba = self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            tipo_prueba=TipoPrueba.AGILIDAD,
            resultado=15.5,
            unidad_medida="s",
        )
        updated = self.dao.update(prueba.id, resultado=14.2)
        self.assertEqual(float(updated.resultado), 14.2)
