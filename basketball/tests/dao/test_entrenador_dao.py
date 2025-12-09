"""
Pruebas unitarias para el DAO EntrenadorDAO
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from basketball.models import Entrenador
from basketball.dao.model_daos import EntrenadorDAO


class EntrenadorDAOTests(TestCase):
    """Pruebas para el DAO de Entrenador usando Mocks"""

    def setUp(self):
        self.dao = EntrenadorDAO()
        self.valid_data = {
            'nombre': 'Laura',
            'apellido': 'Suárez',
            'email': 'laura.suarez@unl.edu.ec',
            'clave': 'password123',
            'dni': '2222222222',
            'rol': 'ENTRENADOR',
            'especialidad': 'Preparador físico',
            'club_asignado': 'Club B'
        }

    @patch.object(Entrenador.objects, 'create')
    def test_create_entrenador(self, mock_create):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.nombre = 'Laura'
        mock_create.return_value = mock_entrenador

        entrenador = self.dao.create(**self.valid_data)

        mock_create.assert_called_once()
        self.assertIsNotNone(entrenador.pk)
        self.assertEqual(entrenador.nombre, 'Laura')

    @patch.object(Entrenador.objects, 'get')
    def test_get_by_id_existente(self, mock_get):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_get.return_value = mock_entrenador

        found = self.dao.get_by_id(1)

        mock_get.assert_called_once_with(pk=1)
        self.assertIsNotNone(found)
        self.assertEqual(found.pk, 1)

    @patch.object(Entrenador.objects, 'get')
    def test_get_by_id_no_existente(self, mock_get):
        from django.core.exceptions import ObjectDoesNotExist
        mock_get.side_effect = ObjectDoesNotExist()

        found = self.dao.get_by_id(99999)

        self.assertIsNone(found)

    @patch.object(Entrenador.objects, 'filter')
    def test_get_activos(self, mock_filter):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.estado = True
        mock_queryset = Mock()
        mock_queryset.count.return_value = 1
        mock_queryset.first.return_value = mock_entrenador
        mock_filter.return_value = mock_queryset

        activos = self.dao.get_activos()

        mock_filter.assert_called_once_with(estado=True)
        self.assertEqual(activos.count(), 1)

    @patch.object(Entrenador.objects, 'get')
    def test_update_entrenador(self, mock_get):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.nombre = 'Laura'
        mock_entrenador.save = Mock()
        mock_get.return_value = mock_entrenador

        updated = self.dao.update(1, nombre='Laura M')

        mock_get.assert_called_once_with(pk=1)
        mock_entrenador.save.assert_called_once()
        self.assertIsNotNone(updated)

    @patch.object(Entrenador.objects, 'get')
    def test_soft_delete(self, mock_get):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.estado = True
        mock_entrenador.save = Mock()
        mock_get.return_value = mock_entrenador

        success = self.dao.soft_delete(1)

        mock_get.assert_called_once_with(pk=1)
        mock_entrenador.save.assert_called_once()
        self.assertTrue(success)

    @patch.object(Entrenador.objects, 'filter')
    def test_email_exists(self, mock_filter):
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        exists = self.dao.email_exists('laura.suarez@unl.edu.ec')

        self.assertTrue(exists)

    @patch.object(Entrenador.objects, 'filter')
    def test_email_not_exists(self, mock_filter):
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        exists = self.dao.email_exists('no.existe@unl.edu.ec')

        self.assertFalse(exists)

    @patch.object(Entrenador.objects, 'filter')
    def test_dni_exists(self, mock_filter):
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset

        exists = self.dao.dni_exists('2222222222')

        self.assertTrue(exists)

    @patch.object(Entrenador.objects, 'filter')
    def test_dni_not_exists(self, mock_filter):
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset

        exists = self.dao.dni_exists('9999999999')

        self.assertFalse(exists)
