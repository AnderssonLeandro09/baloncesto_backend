"""Servicio de negocio para Administrador."""

import logging
from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError
from ..dao.administrador_dao import AdministradorDAO
from ..models import Administrador

logger = logging.getLogger(__name__)


class AdministradorService:
    """Lógica de negocio para administradores."""

    def __init__(self):
        self.dao = AdministradorDAO()

    def create_administrador(self, data: Dict[str, Any]) -> Administrador:
        persona_external = data.get('persona_external')
        if not persona_external:
            raise ValidationError("persona_external es obligatorio")

        if self.dao.exists(persona_external=persona_external):
            raise ValidationError(
                f"Ya existe un administrador con persona_external {persona_external}"
            )

        logger.info("Creando administrador para persona_external=%s", persona_external)
        return self.dao.create(**data)

    def update_administrador(self, pk: int, data: Dict[str, Any]) -> Optional[Administrador]:
        return self.dao.update(pk, **data)

    def delete_administrador(self, pk: int) -> bool:
        administrador = self.dao.update(pk, estado=False)
        return administrador is not None

    def get_administrador_by_id(self, pk: int) -> Optional[Administrador]:
        return self.dao.get_by_id(pk)

    def get_all_administradores(self) -> List[Administrador]:
        return list(self.dao.get_by_filter(estado=True))

    def get_by_persona_external(self, persona_external: str) -> Optional[Administrador]:
        return self.dao.get_by_persona_external(persona_external)
