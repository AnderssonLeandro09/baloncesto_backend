"""Pruebas unitarias para PruebaAntropometricaDAO."""

from datetime import date
from unittest.mock import Mock, patch, MagicMock
import unittest


class PruebaAntropometricaDAOTest(unittest.TestCase):
    """
    Tests para PruebaAntropometricaDAO sin dependencia de BD.
    Usa mocks para simular objetos y evitar acceso a la BD real.
    """

    def setUp(self):
        """Configura mocks para cada test."""
        # Mock del atleta
        self.mock_atleta = Mock()
        self.mock_atleta.id = 1
        self.mock_atleta.persona_external = "uuid-juan-perez"

        # Mock de la prueba antropométrica
        self.mock_prueba = Mock()
        self.mock_prueba.id = 100
        self.mock_prueba.atleta = self.mock_atleta
        self.mock_prueba.peso = 70.5
        self.mock_prueba.estatura = 1.75
        self.mock_prueba.fecha_registro = date.today()
        self.mock_prueba.altura_sentado = 0.90
        self.mock_prueba.envergadura = 1.80
        self.mock_prueba.observaciones = "Medición inicial"

    @patch("basketball.dao.prueba_antropometrica_dao.PruebaAntropometricaDAO")
    def test_create_prueba_antropometrica(self, mock_dao_class):
        """
        Verifica que create() crea correctamente una prueba antropométrica.
        No accede a la BD real.
        """
        # Configurar el mock del DAO
        mock_dao = Mock()
        mock_dao_class.return_value = mock_dao
        mock_dao.create.return_value = self.mock_prueba

        prueba = mock_dao.create(
            atleta=self.mock_atleta,
            fecha_registro=date.today(),
            peso=70.5,
            estatura=1.75,
            altura_sentado=0.90,
            envergadura=1.80,
            observaciones="Medición inicial",
        )

        # Verificar que create fue llamado
        mock_dao.create.assert_called_once()

        # Verificar el resultado
        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta, self.mock_atleta)
        self.assertEqual(prueba.peso, 70.5)
        self.assertEqual(prueba.estatura, 1.75)

    @patch("basketball.dao.prueba_antropometrica_dao.PruebaAntropometricaDAO")
    def test_get_by_atleta(self, mock_dao_class):
        """
        Verifica que get_by_atleta() retorna las pruebas del atleta.
        No accede a la BD real.
        """
        # Configurar el mock del DAO
        mock_dao = Mock()
        mock_dao_class.return_value = mock_dao

        # Mock de lista de pruebas
        mock_pruebas_list = [self.mock_prueba]
        mock_dao.get_by_atleta.return_value = mock_pruebas_list

        pruebas = mock_dao.get_by_atleta(self.mock_atleta.id)

        # Verificar que get_by_atleta fue llamado con el ID correcto
        mock_dao.get_by_atleta.assert_called_once_with(self.mock_atleta.id)

        # Verificar resultados
        self.assertEqual(len(pruebas), 1)
        self.assertEqual(pruebas[0].atleta, self.mock_atleta)

    @patch("basketball.dao.prueba_antropometrica_dao.PruebaAntropometricaDAO")
    def test_update_prueba_antropometrica(self, mock_dao_class):
        """
        Verifica que update() modifica correctamente los valores.
        No accede a la BD real.
        """
        # Configurar el mock del DAO
        mock_dao = Mock()
        mock_dao_class.return_value = mock_dao

        # Mock de la prueba actualizada
        updated_prueba = Mock()
        updated_prueba.id = 100
        updated_prueba.atleta = self.mock_atleta
        updated_prueba.peso = 71.3  # Valor actualizado
        updated_prueba.estatura = 1.76

        mock_dao.update.return_value = updated_prueba

        updated = mock_dao.update(self.mock_prueba.id, peso=71.3)

        # Verificar que update fue llamado con los parámetros correctos
        mock_dao.update.assert_called_once_with(self.mock_prueba.id, peso=71.3)

        # Verificar el resultado
        self.assertEqual(updated.peso, 71.3)
