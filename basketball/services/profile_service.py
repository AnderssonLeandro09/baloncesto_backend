"""Servicio para el Perfil de Usuario."""

import logging
from typing import Any, Dict, Optional

from .administrador_service import AdministradorService
from .entrenador_service import EntrenadorService
from .estudiante_vinculacion_service import EstudianteVinculacionService

logger = logging.getLogger(__name__)


class ProfileService:
    """Lógica de negocio para el perfil del usuario autenticado."""

    def __init__(self):
        self.admin_service = AdministradorService()
        self.entrenador_service = EntrenadorService()
        self.estudiante_service = EstudianteVinculacionService()

    def get_profile_data(self, user, token: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información completa del perfil según el rol."""
        persona_external = user.pk
        role = user.role

        data = None
        if role == "ADMIN":
            admin = self.admin_service.dao.get_by_persona_external(persona_external)
            if admin:
                data = self.admin_service.get_administrador_by_id(admin.id, token)
        elif role == "ENTRENADOR":
            entrenador = self.entrenador_service.dao.get_by_persona_external(
                persona_external
            )
            if entrenador:
                data = self.entrenador_service.get_entrenador(entrenador.id, token)
        elif role == "ESTUDIANTE_VINCULACION":
            estudiante = self.estudiante_service.dao.get_by_persona_external(
                persona_external
            )
            if estudiante:
                data = self.estudiante_service.get_estudiante(estudiante.id, token)

        if not data:
            return None

        return {"role": role, "email": user.email, "name": user.name, "data": data}
