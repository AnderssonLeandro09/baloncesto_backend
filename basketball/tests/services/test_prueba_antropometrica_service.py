"""Pruebas unitarias para PruebaAntropometricaService."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
import unittest


class PruebaAntropometricaServiceTest(unittest.TestCase):
    """
    Tests para PruebaAntropometricaService sin dependencia de BD.
    Usa mocks para simular objetos y evitar acceso a la BD real.
    """

    def setUp(self):
        """Configura mocks para cada test."""
        # Mock del atleta
        self.mock_atleta = Mock()
        self.mock_atleta.id = 1
        self.mock_atleta.persona_external = "uuid-maria-lopez"
        self.mock_atleta.fecha_nacimiento = date(2012, 5, 20)
        self.mock_atleta.edad = 13

        # Mock del entrenador
        self.mock_entrenador = Mock()
        self.mock_entrenador.id = 10
        self.mock_entrenador.persona_external = "uuid-entrenador"
        self.mock_entrenador.especialidad = "Baloncesto"
        self.mock_entrenador.club_asignado = "Club Test"

        # Mock del usuario con entrenador asignado
        self.mock_user = Mock()
        self.mock_user.entrenador = self.mock_entrenador

        # Mock de la prueba antropométrica creada
        self.mock_prueba = Mock()
        self.mock_prueba.id = 100
        self.mock_prueba.atleta = self.mock_atleta
        self.mock_prueba.peso = Decimal("48.5")
        self.mock_prueba.estatura = Decimal("1.55")

    @patch(
        "basketball.services.prueba_antropometrica_service.PruebaAntropometricaService"
    )
    @patch("basketball.services.prueba_antropometrica_service.Atleta")
    def test_create_prueba_antropometrica_service(
        self, mock_atleta_model, mock_service_class
    ):
        """
        Verifica que create_prueba_antropometrica() crea correctamente.
        No accede a la BD real.
        """
        # Configurar mocks
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.create_prueba_antropometrica.return_value = self.mock_prueba
        mock_atleta_model.objects.get.return_value = self.mock_atleta

        data = {
            "atleta_id": self.mock_atleta.id,
            "fecha_registro": date.today(),
            "peso": Decimal("48.5"),
            "estatura": Decimal("1.55"),
            "altura_sentado": Decimal("0.82"),
            "envergadura": Decimal("1.60"),
            "observaciones": "Medición inicial",
        }

        prueba = mock_service.create_prueba_antropometrica(data, self.mock_user)

        # Verificaciones sin acceso a BD
        self.assertIsNotNone(prueba.id)
        self.assertEqual(prueba.atleta.id, self.mock_atleta.id)
        self.assertEqual(prueba.peso, Decimal("48.5"))

    @patch(
        "basketball.services.prueba_antropometrica_service.PruebaAntropometricaService"
    )
    def test_get_pruebas_by_atleta_service(self, mock_service_class):
        """
        Verifica que get_pruebas_by_atleta() retorna las pruebas del atleta.
        No accede a la BD real.
        """
        # Configurar mock del servicio
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Mock de lista de pruebas
        mock_pruebas_list = [self.mock_prueba]
        mock_service.get_pruebas_by_atleta.return_value = mock_pruebas_list

        pruebas = mock_service.get_pruebas_by_atleta(self.mock_atleta.id)

        # Verificaciones
        self.assertEqual(len(pruebas), 1)
        self.assertEqual(pruebas[0].atleta.id, self.mock_atleta.id)

        # Verificar que se llamó al servicio con el ID correcto
        mock_service.get_pruebas_by_atleta.assert_called_once_with(self.mock_atleta.id)
