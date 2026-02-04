"""Tests del DAO de Administrador usando mocks del ORM."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from basketball.dao.administrador_dao import AdministradorDAO


class AdministradorDAOTests(SimpleTestCase):
    def setUp(self):
        self.dao = AdministradorDAO()

    @patch("basketball.dao.administrador_dao.Administrador.objects")
    def test_get_by_persona_external(self, mock_objects):
        mock_objects.filter.return_value.first.return_value = "admin"

        result = self.dao.get_by_persona_external("ext")

        mock_objects.filter.assert_called_with(persona_external="ext", estado=True)
        self.assertEqual(result, "admin")

    @patch("basketball.dao.administrador_dao.Administrador.objects")
    def test_get_activos(self, mock_objects):
        qs = MagicMock()
        mock_objects.filter.return_value = qs

        result = self.dao.get_activos()

        mock_objects.filter.assert_called_with(estado=True)
        self.assertEqual(result, qs)
