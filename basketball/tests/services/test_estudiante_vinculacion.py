from django.test import TestCase
from unittest.mock import patch, Mock
from basketball.models import EstudianteVinculacion
# Ajusta estas importaciones según la estructura real de tu proyecto si difieren
from basketball.dao.estudiante_vinculacion_dao import EstudianteVinculacionDAO
from basketball.services.estudiante_vinculacion_service import EstudianteVinculacionService
from basketball.utils.result import ResultStatus  # O donde tengas definido ResultStatus

class TestEstudianteVinculacionService(TestCase):
    
    def setUp(self):
        # Inicializamos el servicio y los datos base para usar en los tests
        self.service = EstudianteVinculacionService()
        self.valid_data = {
            "nombre": "Carlos",
            "apellido": "López",
            "email": "carlos.lopez@unl.edu.ec",
            "dni": "3333333333",
            "carrera": "Derecho",
            "semestre": "8",
            "rol": "ESTUDIANTE_VINCULACION"
        }

    @patch.object(EstudianteVinculacionDAO, "email_exists")
    @patch.object(EstudianteVinculacionDAO, "dni_exists")
    @patch.object(EstudianteVinculacionDAO, "create")
    def test_create_estudiante_exitoso(
        self, mock_create, mock_dni_exists, mock_email_exists
    ):
        """Crear estudiante con datos válidos"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = False
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None
        mock_create.return_value = mock_estudiante

        result = self.service.create_estudiante(self.valid_data)

        self.assertTrue(result.is_success)
        self.assertEqual(result.data["nombre"], "Carlos")

    def test_create_estudiante_email_no_institucional(self):
        """Error al crear con email no institucional"""
        self.valid_data["email"] = "carlos@gmail.com"

        result = self.service.create_estudiante(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    def test_create_estudiante_dni_invalido(self):
        """Error al crear con DNI inválido (muy corto)"""
        self.valid_data["dni"] = "123"

        result = self.service.create_estudiante(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    @patch.object(EstudianteVinculacionDAO, "email_exists")
    def test_create_estudiante_email_duplicado(self, mock_email_exists):
        """Error al crear con email duplicado"""
        mock_email_exists.return_value = True

        result = self.service.create_estudiante(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)

    @patch.object(EstudianteVinculacionDAO, "email_exists")
    @patch.object(EstudianteVinculacionDAO, "dni_exists")
    def test_create_estudiante_dni_duplicado(self, mock_dni_exists, mock_email_exists):
        """Error al crear con DNI duplicado"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = True

        result = self.service.create_estudiante(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.CONFLICT)

    def test_create_estudiante_campos_faltantes(self):
        """Error al crear sin campos requeridos"""
        result = self.service.create_estudiante({"nombre": "Juan"})

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    def test_create_estudiante_semestre_invalido(self):
        """Error al crear con semestre inválido"""
        self.valid_data["semestre"] = "15"

        result = self.service.create_estudiante(self.valid_data)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.VALIDATION_ERROR)

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    def test_get_estudiante_existente(self, mock_get_by_id):
        """Obtener estudiante existente"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None
        mock_get_by_id.return_value = mock_estudiante

        result = self.service.get_estudiante(1)

        self.assertTrue(result.is_success)
        self.assertEqual(result.data["id"], 1)

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    def test_get_estudiante_no_existente(self, mock_get_by_id):
        """Obtener estudiante no existente retorna NOT_FOUND"""
        mock_get_by_id.return_value = None

        result = self.service.get_estudiante(99999)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)

    @patch.object(EstudianteVinculacionDAO, "get_activos")
    def test_list_estudiantes(self, mock_get_activos):
        """Listar todos los estudiantes activos"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None
        mock_get_activos.return_value = [mock_estudiante]

        result = self.service.list_estudiantes()

        self.assertTrue(result.is_success)
        self.assertEqual(len(result.data), 1)

    @patch.object(EstudianteVinculacionDAO, "get_all")
    @patch.object(EstudianteVinculacionDAO, "get_activos")
    def test_list_estudiantes_incluyendo_inactivos(
        self, mock_get_activos, mock_get_all
    ):
        """Listar estudiantes incluyendo inactivos"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = False
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None

        mock_get_activos.return_value = []
        mock_get_all.return_value = [mock_estudiante]

        result_activos = self.service.list_estudiantes(solo_activos=True)
        self.assertEqual(len(result_activos.data), 0)

        result_todos = self.service.list_estudiantes(solo_activos=False)
        self.assertEqual(len(result_todos.data), 1)

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    @patch.object(EstudianteVinculacionDAO, "update")
    def test_update_estudiante_exitoso(self, mock_update, mock_get_by_id):
        """Actualizar estudiante existente"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos Alberto"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None
        mock_get_by_id.return_value = mock_estudiante
        mock_update.return_value = mock_estudiante

        result = self.service.update_estudiante(1, {"nombre": "Carlos Alberto"})

        self.assertTrue(result.is_success)
        self.assertEqual(result.data["nombre"], "Carlos Alberto")

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    def test_update_estudiante_no_existente(self, mock_get_by_id):
        """Error al actualizar estudiante no existente"""
        mock_get_by_id.return_value = None

        result = self.service.update_estudiante(99999, {"nombre": "Test"})

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    @patch.object(EstudianteVinculacionDAO, "soft_delete")
    def test_delete_estudiante_exitoso(self, mock_soft_delete, mock_get_by_id):
        """Dar de baja estudiante activo"""
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.estado = True  # Estudiante activo
        mock_get_by_id.return_value = mock_estudiante
        mock_soft_delete.return_value = True

        result = self.service.delete_estudiante(1)

        self.assertTrue(result.is_success)
        self.assertFalse(result.data["estado"])

    @patch.object(EstudianteVinculacionDAO, "get_by_id")
    def test_delete_estudiante_no_existente(self, mock_get_by_id):
        """Error al dar de baja estudiante no existente"""
        mock_get_by_id.return_value = None

        result = self.service.delete_estudiante(99999)

        self.assertFalse(result.is_success)
        self.assertEqual(result.status, ResultStatus.NOT_FOUND)

    @patch.object(EstudianteVinculacionDAO, "email_exists")
    @patch.object(EstudianteVinculacionDAO, "dni_exists")
    @patch.object(EstudianteVinculacionDAO, "create")
    def test_email_normalizado_a_minusculas(
        self, mock_create, mock_dni_exists, mock_email_exists
    ):
        """El email se normaliza a minúsculas"""
        mock_email_exists.return_value = False
        mock_dni_exists.return_value = False
        mock_estudiante = Mock(spec=EstudianteVinculacion)
        mock_estudiante.pk = 1
        mock_estudiante.id = 1
        mock_estudiante.nombre = "Carlos"
        mock_estudiante.apellido = "López"
        mock_estudiante.email = "carlos.lopez@unl.edu.ec"
        mock_estudiante.dni = "3333333333"
        mock_estudiante.carrera = "Derecho"
        mock_estudiante.semestre = "8"
        mock_estudiante.estado = True
        mock_estudiante.foto_perfil = None
        mock_estudiante.rol = "ESTUDIANTE_VINCULACION"
        mock_estudiante.fecha_registro = None
        mock_create.return_value = mock_estudiante

        self.valid_data["email"] = "CARLOS.LOPEZ@UNL.EDU.EC"
        result = self.service.create_estudiante(self.valid_data)

        self.assertTrue(result.is_success)