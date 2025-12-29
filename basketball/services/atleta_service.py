"""Servicio de negocio para Atleta."""

import logging
from django.conf import settings
from ..dao.atleta_dao import AtletaDAO
from ..dao.inscripcion_dao import InscripcionDAO

logger = logging.getLogger(__name__)


class AtletaService:
    """Lógica de negocio para atletas."""

    def __init__(self):
        self.atleta_dao = AtletaDAO()
        self.inscripcion_dao = InscripcionDAO()
        self.user_module_url = settings.USER_MODULE_URL.rstrip("/")

    # TODO: Implementar métodos específicos de Atleta que no sean de Inscripción
    # (ej: gestión de pruebas físicas, antropométricas, etc.)
    pass
