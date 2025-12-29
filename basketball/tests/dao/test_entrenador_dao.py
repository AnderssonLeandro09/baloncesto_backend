"""Tests del DAO de Entrenador."""

from django.test import TestCase
from ...models import Entrenador
from ...dao.entrenador_dao import EntrenadorDAO


class EntrenadorDAOTests(TestCase):
    def setUp(self):
        self.dao = EntrenadorDAO()
        self.entrenador = Entrenador.objects.create(
            persona_external="ext-123",
            especialidad="Táctica",
            club_asignado="Club A",
            eliminado=False,
        )

    def test_get_activos(self):
        # Crear uno eliminado
        Entrenador.objects.create(
            persona_external="ext-456",
            especialidad="Físico",
            club_asignado="Club B",
            eliminado=True,
        )
        activos = self.dao.get_activos()
        self.assertEqual(len(activos), 1)
        self.assertEqual(activos[0].persona_external, "ext-123")

    def test_get_by_persona_external(self):
        found = self.dao.get_by_persona_external("ext-123")
        self.assertIsNotNone(found)
        self.assertEqual(found.especialidad, "Táctica")

    def test_get_by_persona_external_not_found(self):
        found = self.dao.get_by_persona_external("non-existent")
        self.assertIsNone(found)
