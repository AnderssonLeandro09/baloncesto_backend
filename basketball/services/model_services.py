"""
Servicios específicos para cada entidad del módulo Basketball

TODO: Implementar servicios para cada modelo
"""

import logging
from decimal import Decimal
from typing import List, Optional
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.exceptions import NotFound

from ..dao.model_daos import PruebaAntropometricaDAO
from ..models import PruebaAntropometrica, Atleta, Inscripcion

logger = logging.getLogger(__name__)


class PruebaAntropometricaServiceException(Exception):
    """Excepción personalizada para PruebaAntropometricaService"""
    pass


class PruebaAntropometricaService:
    """
    Servicio de negocio para Pruebas Antropométricas
    """

    def __init__(self):
        self.dao = PruebaAntropometricaDAO()

    def _calcular_imc(self, peso: Decimal, estatura_cm: Decimal) -> Decimal:
        """
        Calcula el Índice de Masa Corporal (convierte estatura de cm a m)
        """
        estatura_m = estatura_cm / Decimal('100')
        if estatura_m <= 0:
            raise PruebaAntropometricaServiceException("Estatura debe ser positiva para calcular IMC")
        return round(peso / (estatura_m ** 2), 2)

    def _calcular_indice_cormico(self, altura_sentado_cm: Decimal, estatura_cm: Decimal) -> Decimal:
        """
        Calcula el Índice Córmico (convierte medidas de cm a m)
        """
        estatura_m = estatura_cm / Decimal('100')
        altura_sentado_m = altura_sentado_cm / Decimal('100')
        if estatura_m <= 0:
            raise PruebaAntropometricaServiceException("Estatura debe ser positiva para calcular índice córmico")
        return round((altura_sentado_m / estatura_m) * 100, 2)

    def _validar_inscripcion_atleta(self, atleta_id: int) -> None:
        """
        Valida que el atleta tenga una inscripción habilitada
        """
        try:
            inscripcion = Inscripcion.objects.get(atleta_id=atleta_id, habilitada=True)
        except Inscripcion.DoesNotExist:
            raise PruebaAntropometricaServiceException("El atleta no tiene una inscripción habilitada")

    def _validar_permisos_usuario(self, user_role: str) -> None:
        """
        Valida que el usuario tenga permisos para registrar pruebas
        """
        if user_role not in ['ENTRENADOR', 'ESTUDIANTE_VINCULACION']:
            raise PermissionDenied("Usuario no autorizado para registrar pruebas antropométricas")

    def _validar_coherencia_datos(self, estatura: Decimal, altura_sentado: Decimal,
                                  envergadura: Decimal, peso: Decimal) -> None:
        """
        Valida la coherencia de los datos antropométricos (en cm)
        """
        if estatura <= 0 or peso <= 0:
            raise ValidationError("Estatura y peso deben ser positivos")

        if altura_sentado > estatura:
            raise ValidationError("Altura sentado no puede ser mayor que estatura")

        if envergadura < estatura - Decimal('5'):  # 5 cm = 0.05 m
            raise ValidationError("Envergadura debe ser al menos estatura - 5 cm")

    def crear_prueba(self, data: dict, user) -> PruebaAntropometrica:
        """
        Crea una nueva prueba antropométrica con validaciones de negocio

        Args:
            data: Datos de la prueba
            user: Usuario autenticado

        Returns:
            PruebaAntropometrica: Prueba creada
        """
        try:
            # Validar permisos
            self._validar_permisos_usuario(user.role)

            # Validar inscripción del atleta
            atleta_id = data.get('atleta')
            self._validar_inscripcion_atleta(atleta_id)

            # Extraer valores
            estatura = data.get('estatura')
            altura_sentado = data.get('altura_sentado')
            envergadura = data.get('envergadura')
            peso = data.get('peso')

            # Validar coherencia
            self._validar_coherencia_datos(estatura, altura_sentado, envergadura, peso)

            # Calcular valores automáticos
            imc = self._calcular_imc(peso, estatura)
            indice_cormico = self._calcular_indice_cormico(altura_sentado, estatura)

            # Preparar datos para creación
            create_data = data.copy()
            create_data['indice_masa_corporal'] = imc
            create_data['indice_cormico'] = indice_cormico

            # Asignar registrador según rol
            if user.role == 'ENTRENADOR':
                # Aquí necesitaríamos mapear el user.pk al entrenador correspondiente
                # Por simplicidad, asumimos que user.pk es el ID del entrenador
                create_data['registrado_por_entrenador_id'] = user.pk
                create_data['rol_registrador'] = 'ENTRENADOR'
            elif user.role == 'ESTUDIANTE_VINCULACION':
                create_data['registrado_por_estudiante_id'] = user.pk
                create_data['rol_registrador'] = 'ESTUDIANTE_VINCULACION'

            return self.dao.create(**create_data)

        except Exception as e:
            logger.error(f"Error al crear prueba antropométrica: {e}")
            raise

    def obtener_por_atleta(self, atleta_id: int) -> List[PruebaAntropometrica]:
        """
        Obtiene todas las pruebas activas de un atleta
        """
        return list(self.dao.get_by_atleta(atleta_id))

    def obtener_por_id(self, prueba_id: int) -> Optional[PruebaAntropometrica]:
        """
        Obtiene una prueba por ID
        """
        return self.dao.get_by_id(prueba_id)

    def obtener_todas_activas(self) -> List[PruebaAntropometrica]:
        """
        Obtiene todas las pruebas activas
        """
        return list(self.dao.get_activas())

    def obtener_datos_grafica(self, atleta_id: int) -> List[dict]:
        """
        Obtiene datos para gráficas (IMC e Índice Córmico por fecha)
        """
        pruebas = self.dao.get_by_atleta(atleta_id)
        return [
            {
                'fecha': prueba.fecha_registro,
                'imc': prueba.indice_masa_corporal,
                'indice_cormico': prueba.indice_cormico,
            }
            for prueba in pruebas
        ]

    def desactivar_prueba(self, prueba_id: int, user) -> bool:
        """
        Desactiva una prueba (no se elimina)
        """
        # Aquí podríamos agregar validaciones adicionales si es necesario
        return self.dao.desactivar(prueba_id)


# TODO: Implementar AtletaService
# TODO: Implementar GrupoAtletaService
# TODO: Implementar InscripcionService
# TODO: Implementar PruebaFisicaService
# TODO: Implementar EntrenadorService
# TODO: Implementar EstudianteVinculacionService
