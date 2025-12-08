"""
Pruebas unitarias para el DAO EstudianteVinculacionDAO
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from basketball.models import EstudianteVinculacion
from basketball.dao.model_daos import EstudianteVinculacionDAO


class EstudianteVinculacionDAOTests(TestCase):
    """Pruebas para el DAO de EstudianteVinculacion usando Mocks"""
    
    def setUp(self):
        self.dao = EstudianteVinculacionDAO()
        self.valid_data = {
            'nombre': 'María',
            'apellido': 'García',
            'email': 'maria.garcia@unl.edu.ec',
            'clave': 'password123',
            'dni': '1111111111',
            'rol': 'ESTUDIANTE_VINCULACION',
            'carrera': 'Medicina',
            'semestre': '5',
        }
    
    @patch.object(EstudianteVinculacion.objects, 'create')
    def test_create_estudiante(self, mock_create):
        """Crear estudiante mediante DAO"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.nombre = 'María'
        mock_create.return_value = mock_estudiante
        
        estudiante = self.dao.create(**self.valid_data)
        
        mock_create.assert_called_once()
        self.assertIsNotNone(estudiante.pk)
        self.assertEqual(estudiante.nombre, 'María')
    
    @patch.object(EstudianteVinculacion.objects, 'get')
    def test_get_by_id_existente(self, mock_get):
        """Obtener estudiante existente por ID"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_get.return_value = mock_estudiante
        
        found = self.dao.get_by_id(1)
        
        mock_get.assert_called_once_with(pk=1)
        self.assertIsNotNone(found)
        self.assertEqual(found.pk, 1)
    
    @patch.object(EstudianteVinculacion.objects, 'get')
    def test_get_by_id_no_existente(self, mock_get):
        """Obtener estudiante no existente devuelve None"""
        from django.core.exceptions import ObjectDoesNotExist
        mock_get.side_effect = ObjectDoesNotExist()
        
        found = self.dao.get_by_id(99999)
        
        self.assertIsNone(found)
    
    @patch.object(EstudianteVinculacion.objects, 'filter')
    def test_get_activos(self, mock_filter):
        """Obtener solo estudiantes activos"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.estado = True
        mock_queryset = Mock()
        mock_queryset.count.return_value = 1
        mock_queryset.first.return_value = mock_estudiante
        mock_filter.return_value = mock_queryset
        
        activos = self.dao.get_activos()
        
        mock_filter.assert_called_once_with(estado=True)
        self.assertEqual(activos.count(), 1)
    
    @patch.object(EstudianteVinculacion.objects, 'get')
    def test_update_estudiante(self, mock_get):
        """Actualizar estudiante"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.nombre = 'María'
        mock_estudiante.semestre = '5'
        mock_estudiante.save = Mock()
        mock_get.return_value = mock_estudiante
        
        updated = self.dao.update(1, nombre='María José', semestre='6')
        
        mock_get.assert_called_once_with(pk=1)
        mock_estudiante.save.assert_called_once()
        self.assertIsNotNone(updated)
    
    @patch.object(EstudianteVinculacion.objects, 'get')
    def test_soft_delete(self, mock_get):
        """Soft delete cambia estado a False"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.estado = True
        mock_estudiante.save = Mock()
        mock_get.return_value = mock_estudiante
        
        success = self.dao.soft_delete(1)
        
        mock_get.assert_called_once_with(pk=1)
        mock_estudiante.save.assert_called_once()
        self.assertTrue(success)
    
    @patch.object(EstudianteVinculacion.objects, 'filter')
    def test_email_exists(self, mock_filter):
        """Verificar si email existe"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset
        
        exists = self.dao.email_exists('maria.garcia@unl.edu.ec')
        
        self.assertTrue(exists)
    
    @patch.object(EstudianteVinculacion.objects, 'filter')
    def test_email_not_exists(self, mock_filter):
        """Verificar si email no existe"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset
        
        exists = self.dao.email_exists('no.existe@unl.edu.ec')
        
        self.assertFalse(exists)
    
    @patch.object(EstudianteVinculacion.objects, 'filter')
    def test_dni_exists(self, mock_filter):
        """Verificar si DNI existe"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_filter.return_value = mock_queryset
        
        exists = self.dao.dni_exists('1111111111')
        
        self.assertTrue(exists)
    
    @patch.object(EstudianteVinculacion.objects, 'filter')
    def test_dni_not_exists(self, mock_filter):
        """Verificar si DNI no existe"""
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        mock_filter.return_value = mock_queryset
        
        exists = self.dao.dni_exists('9999999999')
        
        self.assertFalse(exists)
