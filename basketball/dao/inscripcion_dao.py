from ..models import Inscripcion
from .generic_dao import GenericDAO


class InscripcionDAO(GenericDAO[Inscripcion]):
    model = Inscripcion
