"""Servicio de negocio para GrupoAtleta."""

import logging
from typing import Any, Dict, List, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from ..dao.grupo_atleta_dao import GrupoAtletaDAO
from ..models import GrupoAtleta, Entrenador, Atleta

logger = logging.getLogger(__name__)


class GrupoAtletaService:
    """Lógica de negocio para la gestión de grupos de atletas."""

    def __init__(self):
        self.dao = GrupoAtletaDAO()

    def get_entrenador_from_user(self, user) -> Optional[Entrenador]:
        """Obtiene el entrenador basado en el usuario autenticado.

        Args:
            user: Usuario autenticado con persona_external (user.pk)

        Returns:
            Entrenador o None si no existe

        Raises:
            ValidationError si no se encuentra el entrenador
        """
        if not user or not hasattr(user, "pk"):
            raise ValidationError("Usuario no autenticado")

        persona_external = user.pk

        try:
            entrenador = Entrenador.objects.get(
                persona_external=persona_external, eliminado=False
            )
            return entrenador
        except Entrenador.DoesNotExist:
            raise ValidationError(
                f"No se encontró un entrenador para el usuario {persona_external}"
            )
        except Exception as exc:
            logger.error(f"Error al buscar entrenador: {exc}")
            raise ValidationError("Error al obtener información del entrenador")

    def create_grupo(self, data: Dict[str, Any], user=None) -> GrupoAtleta:
        """Crea un nuevo grupo de atletas y asigna atletas si se proporcionan.

        Args:
            data: Datos del grupo (ya validados por el serializer)
            user: Usuario autenticado (se usará para obtener entrenador)

        Returns:
            GrupoAtleta creado
        """
        with transaction.atomic():
            # Hacer copia defensiva para evitar mutación del dict original
            data = dict(data)

            # Asignar entrenador automáticamente desde el usuario autenticado
            if user:
                entrenador = self.get_entrenador_from_user(user)
                data["entrenador_id"] = entrenador.id
            else:
                raise ValidationError("Usuario autenticado requerido")

            # Remover campos que no deben venir del frontend
            data.pop("entrenador", None)
            data.pop("estado", None)
            data.pop("eliminado", None)
            data.pop("id", None)

            # Validar que el nombre no esté duplicado (case-insensitive)
            nombre = data.get("nombre")
            if nombre:
                if GrupoAtleta.objects.filter(
                    nombre__iexact=nombre, eliminado=False
                ).exists():
                    raise ValidationError(
                        f"Ya existe un grupo con el nombre '{nombre}'"
                    )

            # Validar categoría no vacía
            categoria = data.get("categoria")
            if categoria and not categoria.strip():
                raise ValidationError("La categoría no puede estar vacía")

            # Extraer atletas antes de crear el grupo
            atleta_ids = data.pop("atletas", [])

            # Crear el grupo con estado activo por defecto
            data.setdefault("estado", True)
            grupo = self.dao.create(**data)

            # Asignar atletas si se proporcionaron
            if atleta_ids:
                self._assign_atletas(grupo, atleta_ids)

            return grupo

    def update_grupo(
        self, pk: int, data: Dict[str, Any], user=None
    ) -> Optional[GrupoAtleta]:
        """Actualiza un grupo existente y sus atletas.

        Args:
            pk: ID del grupo a actualizar
            data: Datos a actualizar (ya validados por el serializer)
            user: Usuario autenticado (se valida que sea el dueño del grupo)

        Returns:
            GrupoAtleta actualizado o None si no existe
        """
        with transaction.atomic():
            # Hacer copia defensiva para evitar mutación del dict original
            data = dict(data)

            # Validar que pk sea entero positivo
            try:
                pk = int(pk)
                if pk <= 0:
                    raise ValidationError("ID inválido")
            except (ValueError, TypeError):
                raise ValidationError("ID debe ser un número válido")

            grupo = self.dao.get_by_id_activo(pk)
            if not grupo:
                return None

            # Validar ownership (siempre requerido)
            if not user:
                raise ValidationError("Usuario autenticado requerido")

            entrenador = self.get_entrenador_from_user(user)
            if grupo.entrenador_id != entrenador.id:
                raise ValidationError("No tienes permiso para actualizar este grupo")

            # Remover campos que no deben modificarse
            data.pop("entrenador", None)
            data.pop("entrenador_id", None)
            data.pop("estado", None)
            data.pop("eliminado", None)
            data.pop("id", None)
            data.pop("fecha_creacion", None)

            # Validar que el nombre no esté duplicado (case-insensitive)
            nombre = data.get("nombre")
            if nombre:
                if (
                    GrupoAtleta.objects.filter(nombre__iexact=nombre, eliminado=False)
                    .exclude(id=pk)
                    .exists()
                ):
                    raise ValidationError(
                        f"Ya existe un grupo con el nombre '{nombre}'"
                    )

            # Validar categoría no vacía
            categoria = data.get("categoria")
            if categoria and not categoria.strip():
                raise ValidationError("La categoría no puede estar vacía")

            # Extraer atletas antes de actualizar
            atleta_ids = data.pop("atletas", None)

            # Actualizar el grupo solo si hay datos válidos
            if data:
                updated_grupo = self.dao.update(pk, **data)
            else:
                updated_grupo = grupo

            # Actualizar atletas si se proporcionaron
            if atleta_ids is not None:
                self._assign_atletas(updated_grupo, atleta_ids)

            return updated_grupo

    def _assign_atletas(self, grupo: GrupoAtleta, atleta_ids: List[int]):
        """Asocia una lista de atletas al grupo, validando lógica de negocio.

        Args:
            grupo: Grupo al que se asignarán los atletas
            atleta_ids: Lista de IDs de atletas (ya validados por el serializer)
        """
        # Los atletas ya vienen validados por el serializer (tipo, rango, duplicados)
        # Solo se valida lógica de negocio

        atletas = Atleta.objects.filter(id__in=atleta_ids)

        # Validar que todos los atletas existan
        if len(atletas) != len(atleta_ids):
            raise ValidationError("Algunos atletas no existen")

        # Validar que los atletas cumplan con el rango de edad del grupo
        for atleta in atletas:
            if (
                atleta.edad < grupo.rango_edad_minima
                or atleta.edad > grupo.rango_edad_maxima
            ):
                raise ValidationError(
                    "Algunos atletas no cumplen con el rango de edad del grupo"
                )

        grupo.atletas.set(atletas)

    def list_atletas_elegibles(
        self,
        grupo_id: Optional[int] = None,
        min_edad: Optional[int] = None,
        max_edad: Optional[int] = None,
    ) -> List[Atleta]:
        """Lista atletas que cumplen con el rango de edad de un grupo o rango específico."""
        if grupo_id:
            # Validar tipo de dato
            try:
                grupo_id = int(grupo_id)
                if grupo_id <= 0:
                    raise ValidationError("ID de grupo inválido")
            except (ValueError, TypeError):
                raise ValidationError("ID de grupo debe ser un número válido")

            grupo = self.dao.get_by_id_activo(grupo_id)
            if not grupo:
                raise ValidationError("Grupo no encontrado")
            min_edad = grupo.rango_edad_minima
            max_edad = grupo.rango_edad_maxima

        # Validar tipos y rangos
        if min_edad is not None:
            try:
                min_edad = int(min_edad)
                if min_edad < 0 or min_edad > 150:
                    raise ValidationError("Edad mínima debe estar entre 0 y 150")
            except (ValueError, TypeError):
                raise ValidationError("Edad mínima debe ser un número válido")

        if max_edad is not None:
            try:
                max_edad = int(max_edad)
                if max_edad < 0 or max_edad > 150:
                    raise ValidationError("Edad máxima debe estar entre 0 y 150")
            except (ValueError, TypeError):
                raise ValidationError("Edad máxima debe ser un número válido")

        if min_edad is not None and max_edad is not None:
            if min_edad > max_edad:
                raise ValidationError("Edad mínima no puede ser mayor a la máxima")

        if min_edad is None or max_edad is None:
            raise ValidationError(
                "Se requiere un grupo_id o un rango de edad (min_edad, max_edad)"
            )

        queryset = Atleta.objects.filter(edad__gte=min_edad, edad__lte=max_edad)

        if grupo_id:
            queryset = queryset.exclude(grupos__id=grupo_id)

        return list(queryset)

    def delete_grupo(self, pk: int, user=None) -> bool:
        """Realiza una baja lógica del grupo.

        Args:
            pk: ID del grupo a eliminar
            user: Usuario autenticado (se valida que sea el dueño del grupo)

        Returns:
            True si se eliminó, False si no existe
        """
        # Validar tipo de dato
        try:
            pk = int(pk)
            if pk <= 0:
                raise ValidationError("ID de grupo inválido")
        except (ValueError, TypeError):
            raise ValidationError("ID de grupo debe ser un número válido")

        if user:
            # Validar que el grupo pertenezca al entrenador
            grupo = self.dao.get_by_id_activo(pk)
            if not grupo:
                return False

            entrenador = self.get_entrenador_from_user(user)
            if grupo.entrenador_id != entrenador.id:
                raise ValidationError("No tienes permiso para eliminar este grupo")

        updated = self.dao.update(pk, eliminado=True)
        return updated is not None

    def get_grupo(self, pk: int, user=None) -> Optional[GrupoAtleta]:
        """Obtiene un grupo por su ID.

        Args:
            pk: ID del grupo
            user: Usuario autenticado (opcional, para validar ownership)

        Returns:
            GrupoAtleta o None si no existe
        """
        # Validar tipo de dato
        try:
            pk = int(pk)
            if pk <= 0:
                raise ValidationError("ID de grupo inválido")
        except (ValueError, TypeError):
            raise ValidationError("ID de grupo debe ser un número válido")

        grupo = self.dao.get_by_id_activo(pk)

        # Si se proporciona usuario, validar ownership
        if grupo and user:
            entrenador = self.get_entrenador_from_user(user)
            if grupo.entrenador_id != entrenador.id:
                raise ValidationError("No tienes permiso para ver este grupo")

        return grupo

    def list_grupos_by_user(self, user) -> List[GrupoAtleta]:
        """Lista los grupos del entrenador autenticado.

        Args:
            user: Usuario autenticado

        Returns:
            Lista de grupos del entrenador
        """
        entrenador = self.get_entrenador_from_user(user)
        return list(self.dao.get_by_entrenador(entrenador.id))

    def list_grupos_por_entrenador(self, entrenador_id: int) -> List[GrupoAtleta]:
        """Lista los grupos activos de un entrenador."""
        return list(self.dao.get_by_entrenador(entrenador_id))
