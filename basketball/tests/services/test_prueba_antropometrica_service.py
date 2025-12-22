"""Tests del servicio de PruebaAntropometrica."""

from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from basketball.services.model_services import PruebaAntropometricaService
from basketball.models import PruebaAntropometrica


class PruebaAntropometricaServiceTests(TestCase):
    def setUp(self):
        self.service = PruebaAntropometricaService()
        self.service.dao = MagicMock()

    def test_calcular_imc(self):
        """Test cálculo de IMC (con estatura en cm)"""
        imc = self.service._calcular_imc(Decimal('70'), Decimal('175'))  # 175 cm = 1.75 m
        expected = round(Decimal('70') / (Decimal('1.75') ** 2), 2)
        self.assertEqual(imc, expected)

    def test_calcular_imc_estatura_cero(self):
        """Test IMC con estatura cero lanza excepción"""
        with self.assertRaises(Exception):
            self.service._calcular_imc(Decimal('70'), Decimal('0'))

    def test_calcular_indice_cormico(self):
        """Test cálculo de índice córmico (con medidas en cm)"""
        indice = self.service._calcular_indice_cormico(Decimal('160'), Decimal('175'))  # 160 cm, 175 cm
        expected = round((Decimal('1.60') / Decimal('1.75')) * 100, 2)
        self.assertEqual(indice, expected)

    @patch('basketball.services.model_services.Inscripcion.objects.get')
    def test_validar_inscripcion_habilitada(self, mock_get):
        """Test validación de inscripción habilitada"""
        mock_get.return_value = MagicMock(habilitada=True)
        self.service._validar_inscripcion_atleta(1)  # No debería lanzar excepción

    @patch('basketball.services.model_services.Inscripcion.objects.get')
    def test_validar_inscripcion_no_habilitada(self, mock_get):
        """Test validación falla si inscripción no habilitada"""
        mock_get.side_effect = Exception("DoesNotExist")
        with self.assertRaises(Exception):
            self.service._validar_inscripcion_atleta(1)

    def test_validar_permisos_entrenador(self):
        """Test permisos válidos para entrenador"""
        user = MagicMock(role='ENTRENADOR')
        self.service._validar_permisos_usuario(user.role)  # No debería lanzar

    def test_validar_permisos_estudiante(self):
        """Test permisos válidos para estudiante"""
        user = MagicMock(role='ESTUDIANTE_VINCULACION')
        self.service._validar_permisos_usuario(user.role)  # No debería lanzar

    def test_validar_permisos_invalidos(self):
        """Test permisos inválidos"""
        with self.assertRaises(PermissionDenied):
            self.service._validar_permisos_usuario('ADMIN')

    def test_validar_coherencia_datos_valido(self):
        """Test validación de coherencia con datos válidos (en cm)"""
        self.service._validar_coherencia_datos(
            Decimal('175'), Decimal('160'), Decimal('180'), Decimal('70')
        )  # No debería lanzar

    def test_validar_coherencia_altura_sentado_mayor(self):
        """Test validación falla si altura sentado > estatura"""
        with self.assertRaises(ValidationError):
            self.service._validar_coherencia_datos(
                Decimal('175'), Decimal('180'), Decimal('180'), Decimal('70')
            )

    def test_validar_coherencia_envergadura_pequena(self):
        """Test validación falla si envergadura < estatura - 5 cm"""
        with self.assertRaises(ValidationError):
            self.service._validar_coherencia_datos(
                Decimal('175'), Decimal('160'), Decimal('165'), Decimal('70')
            )

    @patch('basketball.services.model_services.Inscripcion.objects.get')
    def test_crear_prueba_success(self, mock_get):
        """Test creación exitosa de prueba"""
        mock_get.return_value = MagicMock(habilitada=True)
        user = MagicMock(role='ENTRENADOR', pk=1)
        data = {
            'atleta': 1,
            'estatura': Decimal('175'),
            'altura_sentado': Decimal('160'),
            'envergadura': Decimal('180'),
            'peso': Decimal('70'),
            'observaciones': 'Test',
        }
        prueba_mock = MagicMock()
        self.service.dao.create.return_value = prueba_mock

        result = self.service.crear_prueba(data, user)

        self.assertEqual(result, prueba_mock)
        self.service.dao.create.assert_called_once()

    @patch('basketball.services.model_services.Inscripcion.objects.get')
    def test_crear_prueba_sin_inscripcion(self, mock_get):
        """Test creación falla sin inscripción habilitada"""
        mock_get.side_effect = Exception("DoesNotExist")
        user = MagicMock(role='ENTRENADOR')
        data = {'atleta': 1}

        with self.assertRaises(Exception):
            self.service.crear_prueba(data, user)

    def test_obtener_por_atleta(self):
        """Test obtener pruebas por atleta"""
        pruebas = [MagicMock()]
        self.service.dao.get_by_atleta.return_value = pruebas

        result = self.service.obtener_por_atleta(1)

        self.assertEqual(result, pruebas)
        self.service.dao.get_by_atleta.assert_called_with(1)

    def test_desactivar_prueba(self):
        """Test desactivar prueba"""
        self.service.dao.desactivar.return_value = True

        result = self.service.desactivar_prueba(1, MagicMock())

        self.assertTrue(result)
        self.service.dao.desactivar.assert_called_with(1)