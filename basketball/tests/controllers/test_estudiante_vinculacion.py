"""
Pruebas unitarias para los controllers/endpoints de EstudianteVinculacion
"""

from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from basketball.services.estudiante_vinculacion_service import EstudianteVinculacionService
from basketball.services.base_service import ServiceResult


class EstudianteVinculacionAPITests(APITestCase):
    """Pruebas para los endpoints del API usando Mocks"""
    
    def setUp(self):
        self.base_url = '/api/basketball/estudiantes-vinculacion/'
        self.valid_data = {
            'nombre': 'Ana',
            'apellido': 'Martínez',
            'email': 'ana.martinez@unl.edu.ec',
            'clave': 'password123',
            'dni': '5555555555',
            'carrera': 'Enfermería',
            'semestre': '4',
        }
        self.mock_estudiante_data = {
            'id': 1,
            'nombre': 'Ana',
            'apellido': 'Martínez',
            'email': 'ana.martinez@unl.edu.ec',
            'dni': '5555555555',
            'carrera': 'Enfermería',
            'semestre': '4',
            'estado': True,
            'foto_perfil': None
        }
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_listar_estudiantes_vacio(self, MockService):
        """GET lista vacía de estudiantes"""
        mock_service = MockService.return_value
        mock_service.listar_estudiantes.return_value = ServiceResult.success([])
        
        response = self.client.get(self.base_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_crear_estudiante_exitoso(self, MockService):
        """POST crear estudiante válido"""
        mock_service = MockService.return_value
        mock_service.crear_estudiante.return_value = ServiceResult.success(self.mock_estudiante_data)
        
        response = self.client.post(self.base_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['nombre'], 'Ana')
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_crear_estudiante_email_invalido(self, MockService):
        """POST crear estudiante con email no institucional"""
        mock_service = MockService.return_value
        mock_service.crear_estudiante.return_value = ServiceResult.validation_error(
            "El email debe ser institucional (@unl.edu.ec)"
        )
        
        self.valid_data['email'] = 'ana@gmail.com'
        response = self.client.post(self.base_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_crear_estudiante_duplicado(self, MockService):
        """POST crear estudiante con email duplicado"""
        mock_service = MockService.return_value
        mock_service.crear_estudiante.return_value = ServiceResult.conflict(
            "Ya existe un usuario con este email"
        )
        
        response = self.client.post(self.base_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_obtener_estudiante_existente(self, MockService):
        """GET obtener estudiante por ID"""
        mock_service = MockService.return_value
        mock_service.obtener_estudiante.return_value = ServiceResult.success(self.mock_estudiante_data)
        
        response = self.client.get(f'{self.base_url}1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], 1)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_obtener_estudiante_no_existente(self, MockService):
        """GET estudiante no existente devuelve 404"""
        mock_service = MockService.return_value
        mock_service.obtener_estudiante.return_value = ServiceResult.not_found(
            "Estudiante de vinculación no encontrado"
        )
        
        response = self.client.get(f'{self.base_url}99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_actualizar_estudiante_exitoso(self, MockService):
        """PUT actualizar estudiante"""
        mock_service = MockService.return_value
        updated_data = self.mock_estudiante_data.copy()
        updated_data['nombre'] = 'Ana María'
        mock_service.actualizar_estudiante.return_value = ServiceResult.success(updated_data)
        
        response = self.client.put(f'{self.base_url}1/', {'nombre': 'Ana María'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nombre'], 'Ana María')
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_dar_de_baja_estudiante(self, MockService):
        """DELETE dar de baja estudiante"""
        mock_service = MockService.return_value
        deleted_data = self.mock_estudiante_data.copy()
        deleted_data['estado'] = False
        mock_service.dar_de_baja.return_value = ServiceResult.success(deleted_data)
        
        response = self.client.delete(f'{self.base_url}1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['estado'])
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_reactivar_estudiante(self, MockService):
        """POST reactivar estudiante dado de baja"""
        mock_service = MockService.return_value
        mock_service.reactivar_estudiante.return_value = ServiceResult.success(self.mock_estudiante_data)
        
        response = self.client.post(f'{self.base_url}1/reactivar/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['estado'])
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_listar_solo_activos(self, MockService):
        """GET listar solo estudiantes activos"""
        mock_service = MockService.return_value
        mock_service.listar_estudiantes.return_value = ServiceResult.success([])
        
        response = self.client.get(self.base_url, {'solo_activos': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)
    
    @patch('basketball.controllers.estudiante_vinculacion_controller.EstudianteVinculacionService')
    def test_listar_incluyendo_inactivos(self, MockService):
        """GET listar incluyendo inactivos"""
        mock_service = MockService.return_value
        inactive_data = self.mock_estudiante_data.copy()
        inactive_data['estado'] = False
        mock_service.listar_estudiantes.return_value = ServiceResult.success([inactive_data])
        
        response = self.client.get(self.base_url, {'solo_activos': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
