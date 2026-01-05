"""Servicio de negocio para Prueba Antropométrica."""

import logging
from typing import List, Optional
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from ..dao.prueba_antropometrica_dao import PruebaAntropometricaDAO
from ..models import PruebaAntropometrica, Atleta

logger = logging.getLogger(__name__)


class PruebaAntropometricaService:
    """Lógica de negocio para pruebas antropométricas."""

    def __init__(self):
        self.dao = PruebaAntropometricaDAO()

    def get_all_pruebas_antropometricas(self) -> List[PruebaAntropometrica]:
        """Obtiene todas las pruebas antropométricas."""
        return list(self.dao.get_all())

    def get_prueba_antropometrica_by_id(
        self, pk: int
    ) -> Optional[PruebaAntropometrica]:
        """Obtiene una prueba antropométrica por su ID."""
        return self.dao.get_by_id(pk)

    def create_prueba_antropometrica(self, data: dict, user) -> PruebaAntropometrica:
        """Crea una nueva prueba antropométrica."""
        try:
            # Soportar tanto 'atleta_id' como 'atleta' del frontend
            atleta_id = data.pop("atleta_id", None) or data.pop("atleta", None)
            if not atleta_id:
                raise ValidationError("El ID del atleta es requerido")

            if not Atleta.objects.filter(id=atleta_id).exists():
                raise ValidationError("El atleta no existe")

            # Determinar tipo de registrador
            registrador = None
            rol = "ENTRENADOR"
            content_type = None
            object_id = None

            if hasattr(user, "entrenador"):
                registrador = user.entrenador
                rol = "ENTRENADOR"
                content_type = ContentType.objects.get_for_model(registrador.__class__)
                object_id = registrador.id
            elif hasattr(user, "estudiantevinculacion"):
                registrador = user.estudiantevinculacion
                rol = "ESTUDIANTE_VINCULACION"
                content_type = ContentType.objects.get_for_model(registrador.__class__)
                object_id = registrador.id

            data.update(
                {
                    "atleta_id": atleta_id,
                    "content_type": content_type,
                    "object_id": object_id,
                    "rol_registrador": rol,
                }
            )

            return self.dao.create(**data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al crear prueba antropométrica: {e}")
            raise ValidationError(
                f"No se pudo crear la prueba antropométrica: {str(e)}"
            )

    def update_prueba_antropometrica(
        self, pk: int, data: dict, user
    ) -> PruebaAntropometrica:
        """Actualiza una prueba antropométrica existente."""
        try:
            prueba = self.dao.get_by_id(pk)
            if not prueba:
                raise ValidationError("Prueba antropométrica no encontrada")

            # Soportar tanto 'atleta_id' como 'atleta' del frontend
            atleta_id = data.pop("atleta_id", None) or data.pop("atleta", None)
            if atleta_id:
                if not Atleta.objects.filter(id=atleta_id).exists():
                    raise ValidationError("El atleta no existe")
                data["atleta_id"] = atleta_id

            return self.dao.update(pk, **data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error al actualizar prueba antropométrica: {e}")
            raise ValidationError(
                f"No se pudo actualizar la prueba antropométrica: {str(e)}"
            )

    def get_pruebas_antropometricas_by_atleta(
        self, atleta_id: int
    ) -> List[PruebaAntropometrica]:
        """Obtiene todas las pruebas antropométricas de un atleta específico."""
        return list(self.dao.get_by_atleta(atleta_id))

    def get_pruebas_by_atleta(self, atleta_id: int) -> List[PruebaAntropometrica]:
        """Alias requerido por los tests; delega en el método principal."""
        return self.get_pruebas_antropometricas_by_atleta(atleta_id)

    def toggle_estado(self, prueba_id: int) -> PruebaAntropometrica:
        """Cambia el estado de una prueba antropométrica (True -> False o viceversa)."""
        prueba = self.dao.get_by_id(prueba_id)
        if not prueba:
            raise ValidationError("Prueba antropométrica no encontrada")

        return self.dao.update(prueba_id, estado=not prueba.estado)
