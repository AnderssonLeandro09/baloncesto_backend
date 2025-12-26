"""
Servicio de negocio para Inscripciones.
"""

import logging
from typing import Optional
from ..models import Inscripcion
from ..dao.inscripcion_dao import InscripcionDAO

logger = logging.getLogger(__name__)

class InscripcionService:
    """
    Lógica de negocio para la gestión de inscripciones.
    """

    def __init__(self):
        self.dao = InscripcionDAO()

    def cambiar_estado_habilitacion(self, pk: int, habilitada: bool) -> Optional[Inscripcion]:
        """
        Habilita o deshabilita una inscripción (UC-005).
        """
        inscripcion = self.dao.get_by_id(pk)
        if not inscripcion:
            return None
        
        return self.dao.update(pk, habilitada=habilitada)

    def obtener_inscripcion_por_atleta(self, atleta_id: int) -> Optional[Inscripcion]:
        """
        Obtiene la inscripción de un atleta específico.
        """
        resultado = self.dao.get_by_filter(atleta_id=atleta_id)
        return resultado.first() if resultado else None
