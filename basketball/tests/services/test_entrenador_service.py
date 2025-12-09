"""
Pruebas unitarias para el servicio EntrenadorService
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from basketball.models import Entrenador
from basketball.dao.model_daos import EntrenadorDAO
from basketball.services.entrenador_service import EntrenadorService
from basketball.services.base_service import ServiceResult, ResultStatus


class EntrenadorServiceTests(TestCase):
    """Pruebas para el servicio de Entrenador usando Mocks"""

    def setUp(self):
        self.service = EntrenadorService()
        self.valid_data = {
            'nombre': 'Sofia',
            'apellido': 'Ramírez',
            'email': 'sofia.ramirez@unl.edu.ec',
            'clave': 'password123',
            'dni': '4444444444',
            'especialidad': 'Táctica',
            'club_asignado': 'Club C'
        }

    @patch.object(EntrenadorDAO, 'email_exists')
    @patch.object(EntrenadorDAO, 'dni_exists')
    @patch.object(EntrenadorDAO, 'create')
    def test_crear_entrenador_exitoso(self, mock_create, mock_dni_exists, mock_email_exists):
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = False
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.nombre = 'Sofia'
        mock_entrenador.apellido = 'Ramírez'
        mock_entrenador.email = 'sofia.ramirez@unl.edu.ec'
        mock_entrenador.dni = '4444444444'
        mock_entrenador.especialidad = 'Táctica'
        mock_entrenador.club_asignado = 'Club C'
        mock_entrenador.estado = True
        mock_entrenador.foto_perfil = None
        mock_entrenador.rol = 'ENTRENADOR'
        mock_entrenador.fecha_registro = None
        mock_create.return_value = mock_entrenador

        result = self.service.crear_entrenador(self.valid_data)

        self.assertTrue(result.is_success)
        self.assertEqual(result.data['nombre'], 'Sofia')

    def test_crear_entrenador_email_no_institucional(self):
        self.valid_data['email'] = 'sofia@gmail.com'

        result = self.service.crear_entrenador(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    def test_crear_entrenador_dni_invalido(self):
        self.valid_data['dni'] = '123'

        result = self.service.crear_entrenador(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    @patch.object(EntrenadorDAO, 'email_exists')
    def test_crear_entrenador_email_duplicado(self, mock_email_exists):
        mock_email_exists.return_value = True

        result = self.service.crear_entrenador(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)

    @patch.object(EntrenadorDAO, 'email_exists')
    @patch.object(EntrenadorDAO, 'dni_exists')
    def test_crear_entrenador_dni_duplicado(self, mock_dni_exists, mock_email_exists):
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = True

        result = self.service.crear_entrenador(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)

    def test_crear_entrenador_campos_faltantes(self):
        result = self.service.crear_entrenador({'nombre': 'SoloNombre'})

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    @patch.object(EntrenadorDAO, 'get_by_id')
    def test_obtener_entrenador_existente(self, mock_get_by_id):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.nombre = 'Sofia'
        mock_entrenador.apellido = 'Ramírez'
        mock_entrenador.email = 'sofia.ramirez@unl.edu.ec'
        mock_entrenador.dni = '4444444444'
        mock_entrenador.especialidad = 'Táctica'
        mock_entrenador.club_asignado = 'Club C'
        mock_entrenador.estado = True
        mock_entrenador.foto_perfil = None
        mock_entrenador.rol = 'ENTRENADOR'
        mock_entrenador.fecha_registro = None
        mock_get_by_id.return_value = mock_entrenador

        result = self.service.obtener_entrenador(1)

        self.assertTrue(result.is_success)
        self.assertEqual(result.data['id'], 1)

    @patch.object(EntrenadorDAO, 'get_by_id')
    def test_obtener_entrenador_no_existente(self, mock_get_by_id):
        mock_get_by_id.return_value = None

        result = self.service.obtener_entrenador(99999)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)

    @patch.object(EntrenadorDAO, 'get_activos')
    def test_listar_entrenadores(self, mock_get_activos):
        mock_entrenador = Mock(spec=Entrenador)
        mock_entrenador.pk = 1
        mock_entrenador.nombre = 'Sofia'
        mock_entrenador.apellido = 'Ramírez'
        mock_entrenador.email = 'sofia.ramirez@unl.edu.ec'
        mock_entrenador.dni = '4444444444'
        mock_entrenador.especialidad = 'Táctica'
        mock_entrenador.club_asignado = 'Club C'
        mock_entrenador.estado = True
        mock_entrenador.foto_perfil = None
        mock_entrenador.rol = 'ENTRENADOR'
        mock_entrenador.fecha_registro = None
        mock_get_activos.return_value = [mock_entrenador]

        result = self.service.listar_entrenadores()

        self.assertTrue(result.is_success)
        self.assertEqual(len(result.data), 1)
