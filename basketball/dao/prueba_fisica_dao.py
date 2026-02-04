"""DAO para Prueba Física."""

from .generic_dao import GenericDAO
from ..models import PruebaFisica


class PruebaFisicaDAO(GenericDAO[PruebaFisica]):
    """DAO para operaciones CRUD de Prueba Física."""

    model = PruebaFisica

    def get_by_atleta(self, atleta_id: int):
        """Obtiene todas las pruebas físicas de un atleta."""
        return self.get_by_filter(atleta_id=atleta_id, estado=True)
