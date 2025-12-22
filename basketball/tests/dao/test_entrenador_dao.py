"""Tests del DAO de Entrenador usando mocks del ORM."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from basketball.dao.entrenador_dao import EntrenadorDAO


class EntrenadorDAOTests(SimpleTestCase):
    def setUp(self):
        self.dao = EntrenadorDAO()

    @patch("basketball.dao.entrenador_dao.Entrenador.objects")
    def test_get_by_persona_external(self, mock_objects):
        mock_objects.filter.return_value.first.return_value = "entrenador"

        result = self.dao.get_by_persona_external("ext")

        mock_objects.filter.assert_called_with(persona_external="ext", eliminado=False)
        self.assertEqual(result, "entrenador")

    @patch("basketball.dao.entrenador_dao.Entrenador.objects")
    def test_get_activos(self, mock_objects):
        qs = MagicMock()
        mock_objects.filter.return_value = qs

        result = self.dao.get_activos()

        mock_objects.filter.assert_called_with(eliminado=False)
        self.assertEqual(result, qs)