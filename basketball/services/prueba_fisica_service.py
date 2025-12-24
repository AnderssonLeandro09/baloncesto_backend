"""Servicio de negocio para Prueba Física."""

import logging
from typing import List, Optional
from django.core.exceptions import ValidationError
from ..dao.prueba_fisica_dao import PruebaFisicaDAO
from ..models import PruebaFisica

logger = logging.getLogger(__name__)


class PruebaFisicaService:
    """Lógica de negocio para pruebas físicas."""

    def __init__(self):
        self.dao = PruebaFisicaDAO()

    def create_prueba_fisica(self, data: dict) -> PruebaFisica:
        """Crea una nueva prueba física."""
        try:
            # El campo en el modelo es 'atleta', pero recibimos 'atleta_id'
            atleta_id = data.pop("atleta_id", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")
            
            data["atleta_id"] = atleta_id
            return self.dao.create(**data)
        except Exception as e:
            logger.error(f"Error al crear prueba física: {e}")
            raise ValidationError(f"No se pudo crear la prueba física: {e}")

    def update_prueba_fisica(self, prueba_id: int, data: dict) -> PruebaFisica:
        """Actualiza una prueba física existente."""
        try:
            # No permitimos cambiar el atleta en una actualización según requisitos comunes,
            # pero si viene el id lo manejamos.
            if "atleta_id" in data:
                data["atleta_id"] = data.pop("atleta_id")
            
            prueba = self.dao.update(prueba_id, **data)
            if not prueba:
                raise ValidationError("Prueba física no encontrada")
            return prueba
        except Exception as e:
            logger.error(f"Error al actualizar prueba física {prueba_id}: {e}")
            raise ValidationError(f"No se pudo actualizar la prueba física: {e}")

    def get_prueba_fisica_by_id(self, prueba_id: int) -> Optional[PruebaFisica]:
        """Obtiene una prueba física por su ID."""
        return self.dao.get_by_id(prueba_id)

    def get_all_pruebas_fisicas(self) -> List[PruebaFisica]:
        """Obtiene todas las pruebas físicas activas."""
        return list(self.dao.get_by_filter(estado=True))

    def get_pruebas_by_atleta(self, atleta_id: int) -> List[PruebaFisica]:
        """Obtiene todas las pruebas físicas de un atleta específico."""
        return list(self.dao.get_by_atleta(atleta_id))

    def toggle_estado(self, prueba_id: int) -> PruebaFisica:
        """Cambia el estado de una prueba física (True -> False o viceversa)."""
        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError("Prueba física no encontrada")
        
        return self.dao.update(prueba_id, estado=not prueba.estado)
