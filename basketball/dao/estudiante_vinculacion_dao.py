"""DAO para EstudianteVinculacion."""

from typing import Optional
from django.db.models import QuerySet
from .generic_dao import GenericDAO
from ..models import EstudianteVinculacion


class EstudianteVinculacionDAO(GenericDAO[EstudianteVinculacion]):
    """DAO para operaciones CRUD de EstudianteVinculacion."""

    model = EstudianteVinculacion

    def get_by_persona_external(
        self, persona_external: str
    ) -> Optional[EstudianteVinculacion]:
        return self.get_first(persona_external=persona_external, eliminado=False)

    def get_activos(self) -> QuerySet[EstudianteVinculacion]:
        return self.get_by_filter(eliminado=False)
