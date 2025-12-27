"""
DAOs específicos para cada modelo del módulo Basketball

Implementación de DAOs heredando de GenericDAO
"""

from typing import Optional
from django.db.models import QuerySet

from basketball.dao.generic_dao import GenericDAO
from basketball.models import EstudianteVinculacion, Entrenador


class EstudianteVinculacionDAO(GenericDAO[EstudianteVinculacion]):
    """
    DAO específico para el modelo EstudianteVinculacion.
    Proporciona operaciones CRUD y métodos específicos para estudiantes de vinculación.
    """

    model = EstudianteVinculacion

    def get_by_email(self, email: str) -> Optional[EstudianteVinculacion]:
        """
        Obtiene un estudiante por su email.

        Args:
            email: Email del estudiante

        Returns:
            EstudianteVinculacion | None: Estudiante encontrado o None
        """
        return self.get_first(email=email)

    def get_by_dni(self, dni: str) -> Optional[EstudianteVinculacion]:
        """
        Obtiene un estudiante por su DNI.

        Args:
            dni: DNI del estudiante

        Returns:
            EstudianteVinculacion | None: Estudiante encontrado o None
        """
        return self.get_first(dni=dni)

    def get_activos(self) -> QuerySet[EstudianteVinculacion]:
        """
        Obtiene todos los estudiantes activos.

        Returns:
            QuerySet[EstudianteVinculacion]: Estudiantes activos
        """
        return self.get_by_filter(estado=True)

    def get_inactivos(self) -> QuerySet[EstudianteVinculacion]:
        """
        Obtiene todos los estudiantes inactivos (dados de baja).

        Returns:
            QuerySet[EstudianteVinculacion]: Estudiantes inactivos
        """
        return self.get_by_filter(estado=False)

    def get_by_carrera(self, carrera: str) -> QuerySet[EstudianteVinculacion]:
        """
        Obtiene estudiantes por carrera.

        Args:
            carrera: Nombre de la carrera

        Returns:
            QuerySet[EstudianteVinculacion]: Estudiantes de la carrera
        """
        return self.get_by_filter(carrera__icontains=carrera, estado=True)

    def get_by_semestre(self, semestre: str) -> QuerySet[EstudianteVinculacion]:
        """
        Obtiene estudiantes por semestre.

        Args:
            semestre: Semestre del estudiante

        Returns:
            QuerySet[EstudianteVinculacion]: Estudiantes del semestre
        """
        return self.get_by_filter(semestre=semestre, estado=True)

    def search_estudiantes(self, search_term: str) -> QuerySet[EstudianteVinculacion]:
        """
        Busca estudiantes por nombre, apellido, email o DNI.

        Args:
            search_term: Término de búsqueda

        Returns:
            QuerySet[EstudianteVinculacion]: Estudiantes que coinciden
        """
        return self.search(
            search_fields=["nombre", "apellido", "email", "dni", "carrera"],
            search_term=search_term,
        ).filter(estado=True)

    def email_exists(self, email: str, exclude_pk: int = None) -> bool:
        """
        Verifica si un email ya existe.

        Args:
            email: Email a verificar
            exclude_pk: ID a excluir de la verificación (para updates)

        Returns:
            bool: True si el email existe
        """
        queryset = self.model.objects.filter(email=email)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()

    def dni_exists(self, dni: str, exclude_pk: int = None) -> bool:
        """
        Verifica si un DNI ya existe.

        Args:
            dni: DNI a verificar
            exclude_pk: ID a excluir de la verificación (para updates)

        Returns:
            bool: True si el DNI existe
        """
        queryset = self.model.objects.filter(dni=dni)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()


# EntrenadorDAO
class EntrenadorDAO(GenericDAO[Entrenador]):
    """
    DAO específico para el modelo Entrenador.
    Proporciona operaciones CRUD y métodos auxiliares específicos para entrenadores.
    """

    model = Entrenador

    def get_by_email(self, email: str) -> Optional[Entrenador]:
        """Obtiene un entrenador por email."""
        return self.get_first(email=email)

    def email_exists(self, email: str, exclude_pk: int = None) -> bool:
        """Verifica si un email ya existe (opcionalmente excluyendo una PK)."""
        queryset = self.model.objects.filter(email=email)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()

    def dni_exists(self, dni: str, exclude_pk: int = None) -> bool:
        """Verifica si un DNI ya existe (opcionalmente excluyendo una PK)."""
        queryset = self.model.objects.filter(dni=dni)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()

    def get_activos(self) -> QuerySet[Entrenador]:
        """Obtiene todos los entrenadores activos."""
        return self.get_by_filter(estado=True)

    def search_entrenadores(self, search_term: str) -> QuerySet[Entrenador]:
        """Busca entrenadores por nombre, apellido, email, dni, especialidad o club."""
        return self.search(
            search_fields=[
                "nombre",
                "apellido",
                "email",
                "dni",
                "especialidad",
                "club_asignado",
            ],
            search_term=search_term,
        ).filter(estado=True)


# TODO: Implementar AtletaDAO
# TODO: Implementar GrupoAtletaDAO
# TODO: Implementar InscripcionDAO
# TODO: Implementar PruebaAntropometricaDAO
# TODO: Implementar PruebaFisicaDAO
# TODO: Implementar UsuarioDAO
