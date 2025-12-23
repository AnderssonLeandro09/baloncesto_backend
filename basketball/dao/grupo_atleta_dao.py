"""DAO para GrupoAtleta."""

from typing import Optional
from django.db.models import QuerySet
from .generic_dao import GenericDAO
from ..models import GrupoAtleta


class GrupoAtletaDAO(GenericDAO[GrupoAtleta]):
    """DAO para operaciones CRUD de GrupoAtleta."""

    model = GrupoAtleta

    def get_activos(self) -> QuerySet[GrupoAtleta]:
        """Retorna todos los grupos que no han sido eliminados."""
        return self.get_by_filter(eliminado=False)

    def get_by_id_activo(self, grupo_id: int) -> Optional[GrupoAtleta]:
        """Retorna un grupo por ID si no ha sido eliminado."""
        return self.get_first(id=grupo_id, eliminado=False)

    def get_by_entrenador(self, entrenador_id: int) -> QuerySet[GrupoAtleta]:
        """Retorna los grupos asignados a un entrenador específico."""
        return self.get_by_filter(entrenador_id=entrenador_id, eliminado=False)
