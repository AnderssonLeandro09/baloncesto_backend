"""DAO para Entrenador."""

from typing import List, Optional
from ..models import Entrenador
from .generic_dao import GenericDAO


class EntrenadorDAO(GenericDAO[Entrenador]):
    """Acceso a datos para Entrenadores."""

    model = Entrenador

    def get_activos(self) -> List[Entrenador]:
        """Retorna todos los entrenadores que no han sido eliminados."""
        return list(self.model.objects.filter(eliminado=False))

    def get_by_persona_external(self, persona_external: str) -> Optional[Entrenador]:
        """Busca un entrenador por su external ID de persona."""
        try:
            return self.model.objects.get(
                persona_external=persona_external, eliminado=False
            )
        except self.model.DoesNotExist:
            return None
