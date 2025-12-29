"""DAO para Entrenador."""

from typing import Optional
from django.db.models import QuerySet
from .generic_dao import GenericDAO
from ..models import Entrenador


class EntrenadorDAO(GenericDAO[Entrenador]):
    """DAO para operaciones CRUD de Entrenador."""

    model = Entrenador

    def get_by_persona_external(self, persona_external: str) -> Optional[Entrenador]:
        return self.get_first(persona_external=persona_external, eliminado=False)

    def get_activos(self) -> QuerySet[Entrenador]:
        return self.get_by_filter(eliminado=False)
