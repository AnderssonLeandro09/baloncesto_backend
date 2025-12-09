"""
Pruebas unitarias para el servicio EstudianteVinculacionService
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from basketball.models import EstudianteVinculacion
from basketball.dao.model_daos import EstudianteVinculacionDAO
from basketball.services.estudiante_vinculacion_service import EstudianteVinculacionService
from basketball.services.base_service import ServiceResult, ResultStatus


class EstudianteVinculacionServiceTests(TestCase):
    """Pruebas para el servicio de EstudianteVinculacion usando Mocks"""
    
    def setUp(self):
        self.service = EstudianteVinculacionService()
        self.valid_data = {
            'nombre': 'Carlos',
            'apellido': 'López',
            'email': 'carlos.lopez@unl.edu.ec',
            'clave': 'password123',
            'dni': '3333333333',
            'carrera': 'Derecho',
            'semestre': '8',
        }
    
    @patch.object(EstudianteVinculacionDAO, 'email_exists')
    @patch.object(EstudianteVinculacionDAO, 'dni_exists')
    @patch.object(EstudianteVinculacionDAO, 'create')
    def test_crear_estudiante_exitoso(self, mock_create, mock_dni_exists, mock_email_exists):
        """Crear estudiante con datos válidos"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = False
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        mock_create.return_value = mock_estudiante
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data['nombre'], 'Carlos')
    
    def test_crear_estudiante_email_no_institucional(self):
        """Error al crear con email no institucional"""
        self.valid_data['email'] = 'carlos@gmail.com'
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)
    
    def test_crear_estudiante_dni_invalido(self):
        """Error al crear con DNI inválido (muy corto)"""
        self.valid_data['dni'] = '123'
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)
    
    @patch.object(EstudianteVinculacionDAO, 'email_exists')
    def test_crear_estudiante_email_duplicado(self, mock_email_exists):
        """Error al crear con email duplicado"""
        mock_email_exists.return_value = True
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)
    
    @patch.object(EstudianteVinculacionDAO, 'email_exists')
    @patch.object(EstudianteVinculacionDAO, 'dni_exists')
    def test_crear_estudiante_dni_duplicado(self, mock_dni_exists, mock_email_exists):
        """Error al crear con DNI duplicado"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = True
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)
    
    def test_crear_estudiante_campos_faltantes(self):
        """Error al crear sin campos requeridos"""
        result = self.service.crear_estudiante({'nombre': 'Juan'})
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)
    
    def test_crear_estudiante_semestre_invalido(self):
        """Error al crear con semestre inválido"""
        self.valid_data['semestre'] = '15'
        
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    def test_obtener_estudiante_existente(self, mock_get_by_id):
        """Obtener estudiante existente"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        mock_get_by_id.return_value = mock_estudiante
        
        result = self.service.obtener_estudiante(1)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data['id'], 1)
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    def test_obtener_estudiante_no_existente(self, mock_get_by_id):
        """Obtener estudiante no existente retorna NOT_FOUND"""
        mock_get_by_id.return_value = None
        
        result = self.service.obtener_estudiante(99999)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)
    
    @patch.object(EstudianteVinculacionDAO, 'get_activos')
    def test_listar_estudiantes(self, mock_get_activos):
        """Listar todos los estudiantes activos"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        mock_get_activos.return_value = [mock_estudiante]
        
        result = self.service.listar_estudiantes()
        
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.data), 1)
    
    @patch.object(EstudianteVinculacionDAO, 'get_all')
    @patch.object(EstudianteVinculacionDAO, 'get_activos')
    def test_listar_estudiantes_incluyendo_inactivos(self, mock_get_activos, mock_get_all):
        """Listar estudiantes incluyendo inactivos"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = False
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        
        mock_get_activos.return_value = []
        mock_get_all.return_value = [mock_estudiante]
        
        result_activos = self.service.listar_estudiantes(solo_activos=True)
        self.assertEqual(len(result_activos.data), 0)
        
        result_todos = self.service.listar_estudiantes(solo_activos=False)
        self.assertEqual(len(result_todos.data), 1)
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    @patch.object(EstudianteVinculacionDAO, 'update')
    def test_actualizar_estudiante_exitoso(self, mock_update, mock_get_by_id):
        """Actualizar estudiante existente"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos Alberto'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        mock_get_by_id.return_value = mock_estudiante
        mock_update.return_value = mock_estudiante
        
        result = self.service.actualizar_estudiante(1, {'nombre': 'Carlos Alberto'})
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.data['nombre'], 'Carlos Alberto')
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    def test_actualizar_estudiante_no_existente(self, mock_get_by_id):
        """Error al actualizar estudiante no existente"""
        mock_get_by_id.return_value = None
        
        result = self.service.actualizar_estudiante(99999, {'nombre': 'Test'})
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    @patch.object(EstudianteVinculacionDAO, 'soft_delete')
    def test_dar_de_baja_exitoso(self, mock_soft_delete, mock_get_by_id):
        """Dar de baja estudiante activo"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.estado = True  # Estudiante activo
        mock_get_by_id.return_value = mock_estudiante
        mock_soft_delete.return_value = True
        
        result = self.service.dar_de_baja(1)
        
        self.assertTrue(result.is_success)
        self.assertFalse(result.data['estado'])
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    def test_dar_de_baja_no_existente(self, mock_get_by_id):
        """Error al dar de baja estudiante no existente"""
        mock_get_by_id.return_value = None
        
        result = self.service.dar_de_baja(99999)
        
        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)
    
    @patch.object(EstudianteVinculacionDAO, 'get_by_id')
    @patch.object(EstudianteVinculacionDAO, 'update')
    def test_reactivar_estudiante_exitoso(self, mock_update, mock_get_by_id):
        """Reactivar estudiante dado de baja"""
        # Mock para get_by_id - estudiante inactivo
        mock_estudiante_inactivo = Mock(spec=EstudianteVinculacion)
        mock_estudiante_inactivo.pk = 1
        mock_estudiante_inactivo.id = 1
        mock_estudiante_inactivo.nombre = 'Carlos'
        mock_estudiante_inactivo.apellido = 'López'
        mock_estudiante_inactivo.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante_inactivo.dni = '3333333333'
        mock_estudiante_inactivo.carrera = 'Derecho'
        mock_estudiante_inactivo.semestre = '8'
        mock_estudiante_inactivo.estado = False  # Estudiante inactivo
        mock_estudiante_inactivo.foto_perfil = None
        mock_estudiante_inactivo.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante_inactivo.fecha_registro = None
        mock_get_by_id.return_value = mock_estudiante_inactivo
        
        # Mock para update - estudiante reactivado
        mock_estudiante_activo = Mock(spec=EstudianteVinculacion)
        mock_estudiante_activo.pk = 1
        mock_estudiante_activo.id = 1
        mock_estudiante_activo.nombre = 'Carlos'
        mock_estudiante_activo.apellido = 'López'
        mock_estudiante_activo.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante_activo.dni = '3333333333'
        mock_estudiante_activo.carrera = 'Derecho'
        mock_estudiante_activo.semestre = '8'
        mock_estudiante_activo.estado = True  # Estudiante reactivado
        mock_estudiante_activo.foto_perfil = None
        mock_estudiante_activo.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante_activo.fecha_registro = None
        mock_update.return_value = mock_estudiante_activo
        
        result = self.service.reactivar_estudiante(1)
        
        self.assertTrue(result.is_success)
        self.assertTrue(result.data['estado'])
    
    @patch.object(EstudianteVinculacionDAO, 'email_exists')
    @patch.object(EstudianteVinculacionDAO, 'dni_exists')
    @patch.object(EstudianteVinculacionDAO, 'create')
    def test_email_normalizado_a_minusculas(self, mock_create, mock_dni_exists, mock_email_exists):
        """El email se normaliza a minúsculas"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = False
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = 'Carlos'
        mock_estudiante.apellido = 'López'
        mock_estudiante.email = 'carlos.lopez@unl.edu.ec'
        mock_estudiante.dni = '3333333333'
        mock_estudiante.carrera = 'Derecho'
        mock_estudiante.semestre = '8'
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = 'ESTUDIANTE_VINCULACION'
        mock_estudiante.fecha_registro = None
        mock_create.return_value = mock_estudiante
        
        self.valid_data['email'] = 'CARLOS.LOPEZ@UNL.EDU.EC'
        result = self.service.crear_estudiante(self.valid_data)
        
        self.assertTrue(result.is_success)
        # Verificar que el email se pasó en minúsculas al DAO
        call_args = mock_create.call_args
        self.assertEqual(call_args[1]['email'], 'carlos.lopez@unl.edu.ec')
