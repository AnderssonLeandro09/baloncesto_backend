"""Pruebas unitarias para PruebaFisicaService."""

from django.test import TestCase
from ...models import (
    Atleta,
    TipoPrueba,
    Sexo,
    Inscripcion,
    TipoInscripcion,
    GrupoAtleta,
    Entrenador,
)
from ...services.prueba_fisica_service import PruebaFisicaService
from ...dao.prueba_fisica_dao import PruebaFisicaDAO
from datetime import date


class PruebaFisicaServiceTest(TestCase):
    def setUp(self):
        self.service = PruebaFisicaService()

        # Crear entrenador
        self.entrenador = Entrenador.objects.create(
            persona_external="uuid-entrenador-test",
            especialidad="Baloncesto",
        )

        # Crear grupo
        self.grupo = GrupoAtleta.objects.create(
            nombre="Grupo Test",
            rango_edad_minima=10,
            rango_edad_maxima=15,
            categoria="Sub-15",
            entrenador=self.entrenador,
        )

        # Crear atleta
        self.atleta = Atleta.objects.create(
            persona_external="uuid-maria-lopez",
            fecha_nacimiento=date(2012, 5, 20),
            edad=13,
            sexo=Sexo.FEMENINO,
        )

        # Crear inscripción habilitada
        self.inscripcion = Inscripcion.objects.create(
            atleta=self.atleta,
            tipo_inscripcion=TipoInscripcion.MENOR_EDAD,
            fecha_inscripcion=date.today(),
            habilitada=True,
        )

        # Asignar el atleta al grupo
        self.atleta.grupos.add(self.grupo)

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
        # Usar el DAO directamente para verificar
        dao = PruebaFisicaDAO()
        pruebas = dao.get_by_atleta(self.atleta.id)
        self.assertEqual(len(pruebas), 1)
        self.assertEqual(pruebas[0].tipo_prueba, TipoPrueba.VELOCIDAD)
        self.assertEqual(pruebas[0].tipo_prueba, TipoPrueba.VELOCIDAD)
