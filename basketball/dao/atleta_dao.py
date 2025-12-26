from ..models import Atleta
from .generic_dao import GenericDAO

class AtletaDAO(GenericDAO[Atleta]):
    model = Atleta
