"""Tests del DAO de EstudianteVinculacion usando mocks del ORM."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from basketball.dao.estudiante_vinculacion_dao import EstudianteVinculacionDAO


class EstudianteVinculacionDAOTests(SimpleTestCase):
    def setUp(self):
        self.dao = EstudianteVinculacionDAO()

    @patch('basketball.dao.estudiante_vinculacion_dao.EstudianteVinculacion.objects')
    def test_get_by_persona_external(self, mock_objects):
        mock_objects.filter.return_value.first.return_value = 'estudiante'

        result = self.dao.get_by_persona_external('ext')

        mock_objects.filter.assert_called_with(persona_external='ext', eliminado=False)
        self.assertEqual(result, 'estudiante')

    @patch('basketball.dao.estudiante_vinculacion_dao.EstudianteVinculacion.objects')
    def test_get_activos(self, mock_objects):
        qs = MagicMock()
        mock_objects.filter.return_value = qs

        result = self.dao.get_activos()

        mock_objects.filter.assert_called_with(eliminado=False)
        self.assertEqual(result, qs)
