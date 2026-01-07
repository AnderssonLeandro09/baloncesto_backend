"""Tests del servicio de GrupoAtleta usando mocks."""

from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from basketball.services.grupo_atleta_service import GrupoAtletaService, Entrenador


class GrupoAtletaServiceTests(SimpleTestCase):
    def setUp(self):
        # Mock transaction.atomic context manager
        self.mock_atomic = patch("django.db.transaction.atomic").start()
        self.mock_atomic.return_value.__enter__.return_value = None

        self.service = GrupoAtletaService()
        self.service.dao = MagicMock()

    def tearDown(self):
        patch.stopall()

    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_validate_rango_edad_error(self, mock_atleta):
        """Debe fallar si la edad mínima es mayor a la máxima."""
        with self.assertRaises(ValidationError):
            self.service.list_atletas_elegibles(min_edad=15, max_edad=10)

    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_validate_rango_edad_negativo(self, mock_atleta):
        """Debe fallar si la edad mínima es negativa."""
        with self.assertRaises(ValidationError):
            self.service.list_atletas_elegibles(min_edad=-1, max_edad=10)

    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    def test_create_grupo_no_entrenador(self, mock_entrenador):
        """Debe fallar si el entrenador no existe."""
        mock_entrenador.get.side_effect = Entrenador.DoesNotExist()
        user = MagicMock(pk="test_user")

        with self.assertRaises(ValidationError) as cm:
            self.service.create_grupo(
                {
                    "rango_edad_minima": 10,
                    "rango_edad_maxima": 12,
                    "nombre": "Grupo Test",
                },
                user=user,
            )
        self.assertIn("No se encontró un entrenador", str(cm.exception))

    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_create_grupo_success(self, mock_atleta, mock_entrenador, mock_grupo):
        """Debe crear un grupo exitosamente."""
        entrenador_mock = MagicMock(id=1)
        mock_entrenador.get.return_value = entrenador_mock
        user = MagicMock(pk="test_user")

        # Mock para validación de nombre duplicado
        mock_grupo.filter.return_value.exists.return_value = False

        # Mock Atletas
        atleta1 = MagicMock(id=1)
        atleta1.edad = 11
        mock_atleta.filter.return_value = [atleta1]

        grupo_mock = MagicMock()
        grupo_mock.rango_edad_minima = 10
        grupo_mock.rango_edad_maxima = 12
        self.service.dao.create.return_value = grupo_mock

        data = {
            "nombre": "Grupo Test",
            "rango_edad_minima": 10,
            "rango_edad_maxima": 12,
            "atletas": [1],
        }

        result = self.service.create_grupo(data, user=user)

        self.assertEqual(result, grupo_mock)
        self.service.dao.create.assert_called()
        grupo_mock.atletas.set.assert_called()

    @patch("basketball.services.grupo_atleta_service.GrupoAtleta.objects")
    @patch("basketball.services.grupo_atleta_service.Entrenador.objects")
    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_update_grupo_success(self, mock_atleta, mock_entrenador, mock_grupo):
        """Debe actualizar un grupo exitosamente."""
        entrenador_mock = MagicMock(id=1)
        mock_entrenador.get.return_value = entrenador_mock
        user = MagicMock(pk="test_user")

        grupo_mock = MagicMock(
            id=1, entrenador_id=1, rango_edad_minima=10, rango_edad_maxima=12
        )
        self.service.dao.get_by_id_activo.return_value = grupo_mock
        self.service.dao.update.return_value = grupo_mock

        # Mock para validación de nombre duplicado
        mock_grupo.filter.return_value.exclude.return_value.exists.return_value = False

        # Mock Atletas
        atleta1 = MagicMock(id=1)
        atleta1.edad = 11
        mock_atleta.filter.return_value = [atleta1]

        data = {"nombre": "Nombre Nuevo", "atletas": [1]}
        result = self.service.update_grupo(1, data, user=user)

        self.assertEqual(result, grupo_mock)
        self.service.dao.update.assert_called()
        grupo_mock.atletas.set.assert_called()

    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_assign_atletas_edad_invalida(self, mock_atleta):
        """Debe fallar si un atleta no cumple con el rango de edad."""
        grupo_mock = MagicMock(rango_edad_minima=10, rango_edad_maxima=12)
        atleta_viejo = MagicMock(id=1)
        atleta_viejo.edad = 15
        # nombre_atleta y apellido_atleta ya no existen en el modelo
        mock_atleta.filter.return_value = [atleta_viejo]

        with self.assertRaises(ValidationError) as cm:
            self.service._assign_atletas(grupo_mock, [1])
        self.assertIn(
            "Algunos atletas no cumplen con el rango de edad del grupo",
            cm.exception.message,
        )

    def test_delete_grupo(self):
        """Debe llamar al DAO para eliminar lógicamente."""
        self.service.delete_grupo(1)
        self.service.dao.update.assert_called_once_with(1, eliminado=True)

    @patch("basketball.services.grupo_atleta_service.Atleta.objects")
    def test_list_atletas_elegibles(self, mock_atleta):
        """Debe listar atletas que cumplen con el rango de edad."""
        mock_qs = MagicMock()
        # Configurar __iter__ para que list(mock_qs) devuelva la lista deseada
        mock_qs.__iter__.return_value = iter([MagicMock(id=1)])
        mock_atleta.filter.return_value = mock_qs

        result = self.service.list_atletas_elegibles(min_edad=10, max_edad=12)

        self.assertEqual(len(result), 1)
        mock_atleta.filter.assert_called()
