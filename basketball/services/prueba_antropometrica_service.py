"""Servicio de negocio para Prueba Antropométrica."""

import logging
from typing import List
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from ..dao.prueba_antropometrica_dao import PruebaAntropometricaDAO
from ..models import PruebaAntropometrica, Atleta

logger = logging.getLogger(__name__)


class PruebaAntropometricaService:
    """Lógica de negocio para pruebas antropométricas."""

    def __init__(self):
        self.dao = PruebaAntropometricaDAO()

    def create_prueba_antropometrica(self, data: dict, user) -> PruebaAntropometrica:
        """Crea una nueva prueba antropométrica."""
        try:
            atleta_id = data.pop("atleta_id", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")

            if not Atleta.objects.filter(id=atleta_id).exists():
                raise ValidationError("El atleta no existe")

            # Determinar tipo de registrador
            if hasattr(user, "entrenador"):
                registrador = user.entrenador
                rol = "ENTRENADOR"
            elif hasattr(user, "estudiantevinculacion"):
                registrador = user.estudiantevinculacion
                rol = "ESTUDIANTE_VINCULACION"
            else:
                raise ValidationError("Usuario no autorizado para registrar pruebas")

            content_type = ContentType.objects.get_for_model(registrador.__class__)

            data.update(
                {
                    "atleta_id": atleta_id,
                    "content_type": content_type,
                    "object_id": registrador.id,
                    "rol_registrador": rol,
                }
            )

            return self.dao.create(**data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al crear prueba antropométrica: {e}")
            raise ValidationError("No se pudo crear la prueba antropométrica")

    def get_pruebas_by_atleta(self, atleta_id: int) -> List[PruebaAntropometrica]:
        """Obtiene todas las pruebas antropométricas de un atleta específico."""
        return list(self.dao.get_by_atleta(atleta_id))

    def toggle_estado(self, prueba_id: int) -> PruebaAntropometrica:
        """Cambia el estado de una prueba antropométrica (True -> False o viceversa)."""
        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError("Prueba antropométrica no encontrada")

        return self.dao.update(prueba_id, estado=not prueba.estado)
