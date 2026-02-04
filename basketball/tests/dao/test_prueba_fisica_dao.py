"""Pruebas unitarias para PruebaFisicaDAO usando mocks."""

from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch
from ...models import Atleta, TipoPrueba, PruebaFisica
from ...dao.prueba_fisica_dao import PruebaFisicaDAO
from datetime import date


class PruebaFisicaDAOTest(SimpleTestCase):
    def setUp(self):
        self.dao = PruebaFisicaDAO()
        self.atleta = MagicMock(spec=Atleta)
        self.atleta.id = 1
        self.atleta.persona_external = "uuid-juan-perez"

    @patch("basketball.dao.prueba_fisica_dao.PruebaFisica.objects.create")
    def test_create_prueba_fisica(self, mock_create):
        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.atleta = self.atleta
        mock_prueba.resultado = 50.5
        mock_create.return_value = mock_prueba

        prueba = self.dao.create(
            atleta=self.atleta,
            fecha_registro=date.today(),
            tipo_prueba=TipoPrueba.FUERZA,
            resultado=50.5,
            unidad_medida="cm",
            observaciones="Buena fuerza",
        )
        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta, self.atleta)
        self.assertEqual(float(prueba.resultado), 50.5)
        mock_create.assert_called_once()

    @patch("basketball.dao.prueba_fisica_dao.PruebaFisica.objects.filter")
    def test_get_by_atleta(self, mock_filter):
        mock_qs = MagicMock()
        mock_qs.count.return_value = 1
        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.tipo_prueba = TipoPrueba.VELOCIDAD
        mock_qs.__getitem__.return_value = mock_prueba
        mock_filter.return_value = mock_qs

        pruebas = self.dao.get_by_atleta(1)
        self.assertEqual(pruebas.count(), 1)
        self.assertEqual(pruebas[0].tipo_prueba, TipoPrueba.VELOCIDAD)
        mock_filter.assert_called_once()

    @patch("basketball.dao.prueba_fisica_dao.PruebaFisica.objects.get")
    def test_update_prueba_fisica(self, mock_get):
        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_prueba.resultado = 15.5
        mock_get.return_value = mock_prueba

        updated = self.dao.update(1, resultado=14.2)
        self.assertEqual(float(updated.resultado), 14.2)
        mock_get.assert_called_once_with(pk=1)
        mock_prueba.save.assert_called_once()

    @patch("basketball.dao.prueba_fisica_dao.PruebaFisica.objects.get")
    def test_get_by_id(self, mock_get):
        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        mock_get.return_value = mock_prueba

        found = self.dao.get_by_id(1)
        self.assertEqual(found.id, 1)
        mock_get.assert_called_once_with(pk=1)

    @patch("basketball.dao.prueba_fisica_dao.PruebaFisica.objects.get")
    def test_delete_prueba_fisica(self, mock_get):
        mock_prueba = MagicMock(spec=PruebaFisica)
        mock_prueba.id = 1
        # Primero se busca para borrar, luego se busca para verificar que no existe
        mock_get.side_effect = [mock_prueba, PruebaFisica.DoesNotExist]

        self.dao.delete(1)
        found = self.dao.get_by_id(1)
        self.assertIsNone(found)
        mock_prueba.delete.assert_called_once()
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with(pk=1)
