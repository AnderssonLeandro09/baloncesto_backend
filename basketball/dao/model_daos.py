"""
DAOs específicos para cada modelo del módulo Basketball

TODO: Implementar DAOs específicos heredando de GenericDAO
"""

from typing import List, Optional
from django.db.models import QuerySet, Q
from .generic_dao import GenericDAO
from ..models import Atleta, PruebaAntropometrica, Entrenador, EstudianteVinculacion


class PruebaAntropometricaDAO(GenericDAO[PruebaAntropometrica]):
    """
    DAO para operaciones específicas de PruebaAntropometrica
    """

    model = PruebaAntropometrica

    def get_by_atleta(self, atleta_id: int) -> QuerySet[PruebaAntropometrica]:
        """
        Obtiene todas las pruebas antropométricas de un atleta.

        Args:
            atleta_id: ID del atleta

        Returns:
            QuerySet[PruebaAntropometrica]: Pruebas del atleta
        """
        return self.model.objects.filter(atleta_id=atleta_id, estado=True).order_by(
            "-fecha_registro"
        )

    def get_by_registrador(
        self, registrador_id: int, rol: str
    ) -> QuerySet[PruebaAntropometrica]:
        """
        Obtiene pruebas registradas por un usuario específico.

        Args:
            registrador_id: ID del registrador
            rol: Rol del registrador ('ENTRENADOR' o 'ESTUDIANTE_VINCULACION')

        Returns:
            QuerySet[PruebaAntropometrica]: Pruebas registradas
        """
        if rol == "ENTRENADOR":
            return self.model.objects.filter(
                registrado_por_entrenador_id=registrador_id, estado=True
            )
        elif rol == "ESTUDIANTE_VINCULACION":
            return self.model.objects.filter(
                registrado_por_estudiante_id=registrador_id, estado=True
            )
        return self.model.objects.none()

    def get_activas(self) -> QuerySet[PruebaAntropometrica]:
        """
        Obtiene todas las pruebas activas.

        Returns:
            QuerySet[PruebaAntropometrica]: Pruebas activas
        """
        return self.model.objects.filter(estado=True)

    def desactivar(self, prueba_id: int) -> bool:
        """
        Desactiva una prueba antropométrica (no se elimina).

        Args:
            prueba_id: ID de la prueba

        Returns:
            bool: True si se desactivó correctamente
        """
        try:
            prueba = self.get_by_id(prueba_id)
            if prueba:
                prueba.estado = False
                prueba.save()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error al desactivar prueba {prueba_id}: {e}")
            return False


# TODO: Implementar AtletaDAO
# TODO: Implementar GrupoAtletaDAO
# TODO: Implementar InscripcionDAO
# TODO: Implementar PruebaFisicaDAO
# TODO: Implementar EntrenadorDAO
# TODO: Implementar EstudianteVinculacionDAO
# TODO: Implementar UsuarioDAO
