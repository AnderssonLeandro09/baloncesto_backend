"""
Pruebas unitarias para los controllers/endpoints de Entrenador
"""

from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from basketball.services.entrenador_service import EntrenadorService
from basketball.services.base_service import ServiceResult


class EntrenadorAPITests(APITestCase):
    """Pruebas para los endpoints del API de Entrenador usando Mocks"""

    def setUp(self):
        self.base_url = '/api/basketball/entrenadores/'
        self.valid_data = {
            'nombre': 'Pablo',
            'apellido': 'Gómez',
            'email': 'pablo.gomez@unl.edu.ec',
            'clave': 'password123',
            'dni': '7777777777',
            'especialidad': 'Fisioterapia',
            'club_asignado': 'Club A'
        }
        self.mock_entrenador_data = {
            'id': 1,
            'nombre': 'Pablo',
            'apellido': 'Gómez',
            'email': 'pablo.gomez@unl.edu.ec',
            'dni': '7777777777',
            'foto_perfil': None,
            'rol': 'ENTRENADOR',
            'estado': True,
            'fecha_registro': None,
            'especialidad': 'Fisioterapia',
            'club_asignado': 'Club A'
        }

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_listar_entrenadores_vacio(self, MockService):
        mock_service = MockService.return_value
        mock_service.listar_entrenadores.return_value = ServiceResult.success([])

        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data', [])), 0)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_crear_entrenador_exitoso(self, MockService):
        mock_service = MockService.return_value
        mock_service.crear_entrenador.return_value = ServiceResult.success(self.mock_entrenador_data)

        response = self.client.post(self.base_url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['nombre'], 'Pablo')

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_crear_entrenador_email_invalido(self, MockService):
        mock_service = MockService.return_value
        mock_service.crear_entrenador.return_value = ServiceResult.validation_error(
            "El correo debe ser institucional (@unl.edu.ec)"
        )

        self.valid_data['email'] = 'pablo@gmail.com'
        response = self.client.post(self.base_url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_crear_entrenador_duplicado(self, MockService):
        mock_service = MockService.return_value
        mock_service.crear_entrenador.return_value = ServiceResult.conflict(
            "Ya existe un usuario con este email"
        )

        response = self.client.post(self.base_url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_obtener_entrenador_existente(self, MockService):
        mock_service = MockService.return_value
        mock_service.obtener_entrenador.return_value = ServiceResult.success(self.mock_entrenador_data)

        response = self.client.get(f'{self.base_url}1/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], 1)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_obtener_entrenador_no_existente(self, MockService):
        mock_service = MockService.return_value
        mock_service.obtener_entrenador.return_value = ServiceResult.not_found(
            "Entrenador no encontrado"
        )

        response = self.client.get(f'{self.base_url}99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_actualizar_entrenador_exitoso(self, MockService):
        mock_service = MockService.return_value
        updated_data = self.mock_entrenador_data.copy()
        updated_data['nombre'] = 'Pablo Ramón'
        mock_service.actualizar_entrenador.return_value = ServiceResult.success(updated_data)

        response = self.client.put(f'{self.base_url}1/', {'nombre': 'Pablo Ramón'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nombre'], 'Pablo Ramón')

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_dar_de_baja_entrenador(self, MockService):
        mock_service = MockService.return_value
        deleted_data = self.mock_entrenador_data.copy()
        deleted_data['estado'] = False
        mock_service.dar_de_baja.return_value = ServiceResult.success(deleted_data)

        response = self.client.delete(f'{self.base_url}1/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['estado'])

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_reactivar_entrenador(self, MockService):
        mock_service = MockService.return_value
        mock_service.reactivar_entrenador.return_value = ServiceResult.success(self.mock_entrenador_data)

        response = self.client.post(f'{self.base_url}1/reactivar/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['estado'])

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_listar_solo_activos(self, MockService):
        mock_service = MockService.return_value
        mock_service.listar_entrenadores.return_value = ServiceResult.success([])

        response = self.client.get(self.base_url, {'solo_activos': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data', [])), 0)

    @patch('basketball.controllers.entrenador_controller.EntrenadorService')
    def test_listar_incluyendo_inactivos(self, MockService):
        mock_service = MockService.return_value
        inactive_data = self.mock_entrenador_data.copy()
        inactive_data['estado'] = False
        mock_service.listar_entrenadores.return_value = ServiceResult.success([inactive_data])

        response = self.client.get(self.base_url, {'solo_activos': 'false'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data', [])), 1)
