"""Tests del DAO de GrupoAtleta usando mocks del ORM."""

from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from basketball.dao.grupo_atleta_dao import GrupoAtletaDAO


class GrupoAtletaDAOTests(SimpleTestCase):
    def setUp(self):
        self.dao = GrupoAtletaDAO()

    @patch("basketball.dao.grupo_atleta_dao.GrupoAtleta.objects")
    def test_get_activos(self, mock_objects):
        qs = MagicMock()
        mock_objects.filter.return_value.order_by.return_value.__getitem__.return_value = (
            qs
        )

        result = self.dao.get_activos()

        mock_objects.filter.assert_called_with(eliminado=False)
        self.assertEqual(result, qs)

    @patch("basketball.dao.grupo_atleta_dao.GrupoAtleta.objects")
    def test_get_by_id_activo(self, mock_objects):
        mock_objects.filter.return_value.first.return_value = "grupo"

        result = self.dao.get_by_id_activo(1)

        mock_objects.filter.assert_called_with(id=1, eliminado=False)
        self.assertEqual(result, "grupo")

    @patch("basketball.dao.grupo_atleta_dao.GrupoAtleta.objects")
    def test_get_by_entrenador(self, mock_objects):
        qs = MagicMock()
        mock_objects.filter.return_value.order_by.return_value.__getitem__.return_value = (
            qs
        )

        result = self.dao.get_by_entrenador(5)

        mock_objects.filter.assert_called_with(entrenador_id=5, eliminado=False)
        self.assertEqual(result, qs)
