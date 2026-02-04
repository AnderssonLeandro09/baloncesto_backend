"""DAO para Prueba Antropométrica."""

from typing import Optional
from django.contrib.contenttypes.models import ContentType

from .generic_dao import GenericDAO
from ..models import PruebaAntropometrica


class PruebaAntropometricaDAO(GenericDAO[PruebaAntropometrica]):
    """DAO para operaciones CRUD de Prueba Antropométrica."""

    model = PruebaAntropometrica

    def get_by_atleta(self, atleta_id: int):
        """Obtiene todas las pruebas antropométricas activas de un atleta."""
        return self.get_by_filter(atleta_id=atleta_id, estado=True)

    def get_by_registrador(self, registrador):
        """
        Obtiene todas las pruebas antropométricas registradas por un entrenador
        o estudiante de vinculación específico.
        """
        content_type = ContentType.objects.get_for_model(registrador.__class__)
        return self.get_by_filter(
            content_type=content_type,
            object_id=registrador.id,
            estado=True,
        )

    def get_last_by_atleta(self, atleta_id: int) -> Optional[PruebaAntropometrica]:
        """
        Obtiene la última prueba antropométrica registrada de un atleta.
        Útil para reportes, comparaciones y dashboards.
        """
        queryset = self.model.objects.filter(
            atleta_id=atleta_id,
            estado=True,
        ).order_by("-fecha_registro")
        return queryset.first()
