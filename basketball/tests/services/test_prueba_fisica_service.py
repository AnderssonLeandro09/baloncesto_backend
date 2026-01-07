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

    def test_get_persona_info_fallback(self):
        """Prueba que el fallback a datos locales funcione cuando el servicio externo falla."""
        # Mock de _fetch_persona para que retorne None (simulando error)
        from unittest.mock import patch

        # Guardar datos locales en el atleta
        self.atleta.nombres = "Maria"
        self.atleta.apellidos = "Lopez"
        self.atleta.cedula = "1234567890"
        self.atleta.save()

        with patch.object(self.service, "_fetch_persona", return_value=None):
            info = self.service._get_persona_info(self.atleta, "fake-token")

            self.assertEqual(info["nombre"], "Maria")
            self.assertEqual(info["apellido"], "Lopez")
            self.assertEqual(info["identificacion"], "1234567890")

    def test_get_all_pruebas_fisicas_completas(self):
        """Prueba la obtención de todas las pruebas con datos de persona."""
        data = {
            "atleta_id": self.atleta.id,
            "fecha_registro": date.today(),
            "tipo_prueba": TipoPrueba.AGILIDAD,
            "resultado": 15,
        }
        self.service.create_prueba_fisica(data)

        from unittest.mock import patch

        with patch.object(
            self.service,
            "_fetch_persona",
            return_value={
                "data": {
                    "first_name": "Ext",
                    "last_name": "User",
                    "identification": "000",
                }
            },
        ):
            # Simulamos un usuario con rol adecuado
            mock_user = type(
                "obj", (object,), {"role": "ESTUDIANTE_VINCULACION", "pk": "1"}
            )
            results = self.service.get_all_pruebas_fisicas_completas(
                "fake-token", user=mock_user
            )

            self.assertTrue(len(results) >= 1)
            self.assertIn("persona", results[0])
            self.assertIn("semestre", results[0])

    def test_get_atletas_habilitados_con_persona(self):
        """Prueba la obtención de atletas habilitados con su info de persona."""
        from unittest.mock import patch

        with patch.object(self.service, "_fetch_persona", return_value=None):
            mock_user = type(
                "obj", (object,), {"role": "ESTUDIANTE_VINCULACION", "pk": "1"}
            )
            atletas = self.service.get_atletas_habilitados_con_persona(
                "fake-token", user=mock_user
            )

            self.assertTrue(len(atletas) >= 1)
            atleta_info = next(a for a in atletas if a["id"] == self.atleta.id)
            self.assertIsNotNone(atleta_info["persona"])
            # Como mock retorne None, debe usar fallback
            self.assertEqual(
                atleta_info["persona"]["identificacion"], self.atleta.cedula or "N/A"
            )
