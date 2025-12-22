"""
DAO Genérico (Data Access Object) para el módulo Basketball

Proporciona una interfaz genérica para operaciones CRUD sobre los modelos.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from django.db import models, transaction
from django.db.models import QuerySet, Q
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

# Type variable para modelos genéricos
T = TypeVar("T", bound=models.Model)


class GenericDAO(Generic[T]):
    """
    DAO Genérico que proporciona operaciones CRUD básicas para cualquier modelo Django.

    Uso:
        class AtletaDAO(GenericDAO[Atleta]):
            model = Atleta
    """

    model: type[T] = None

    def __init__(self):
        if self.model is None:
            raise ValueError("Debe especificar el modelo en la clase hija")

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    def create(self, **kwargs) -> T:
        """
        Crea una nueva instancia del modelo.

        Args:
            **kwargs: Campos del modelo

        Returns:
            T: Instancia creada
        """
        try:
            instance = self.model.objects.create(**kwargs)
            logger.info(f"{self.model.__name__} creado con ID: {instance.pk}")
            return instance
        except Exception as e:
            logger.error(f"Error al crear {self.model.__name__}: {e}")
            raise

    def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[T]:
        """
        Crea múltiples instancias del modelo.

        Args:
            objects_data: Lista de diccionarios con datos de los objetos

        Returns:
            List[T]: Lista de instancias creadas
        """
        try:
            instances = [self.model(**data) for data in objects_data]
            created = self.model.objects.bulk_create(instances)
            logger.info(f"Creados {len(created)} registros de {self.model.__name__}")
            return created
        except Exception as e:
            logger.error(f"Error en bulk_create de {self.model.__name__}: {e}")
            raise

    # =========================================================================
    # READ Operations
    # =========================================================================

    def get_by_id(self, pk: int) -> Optional[T]:
        """
        Obtiene una instancia por su ID.

        Args:
            pk: Primary key del objeto

        Returns:
            T | None: Instancia encontrada o None
        """
        try:
            return self.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            logger.warning(f"{self.model.__name__} con ID {pk} no encontrado")
            return None

    def get_all(self) -> QuerySet[T]:
        """
        Obtiene todos los registros del modelo.

        Returns:
            QuerySet[T]: QuerySet con todos los registros
        """
        return self.model.objects.all()

    def get_by_filter(self, **filters) -> QuerySet[T]:
        """
        Obtiene registros filtrados por criterios.

        Args:
            **filters: Criterios de filtrado

        Returns:
            QuerySet[T]: QuerySet filtrado
        """
        return self.model.objects.filter(**filters)

    def get_by_q_filter(self, q_filter: Q) -> QuerySet[T]:
        """
        Obtiene registros usando un filtro Q de Django.

        Args:
            q_filter: Filtro Q de Django

        Returns:
            QuerySet[T]: QuerySet filtrado
        """
        return self.model.objects.filter(q_filter)

    def exists(self, **filters) -> bool:
        """
        Verifica si existen registros con los criterios dados.

        Args:
            **filters: Criterios de búsqueda

        Returns:
            bool: True si existe al menos un registro
        """
        return self.model.objects.filter(**filters).exists()

    def count(self, **filters) -> int:
        """
        Cuenta los registros que cumplen los criterios.

        Args:
            **filters: Criterios de filtrado (opcional)

        Returns:
            int: Número de registros
        """
        if filters:
            return self.model.objects.filter(**filters).count()
        return self.model.objects.count()

    def get_first(self, **filters) -> Optional[T]:
        """
        Obtiene el primer registro que cumple los criterios.

        Args:
            **filters: Criterios de filtrado

        Returns:
            T | None: Primera instancia encontrada o None
        """
        return self.model.objects.filter(**filters).first()

    def get_last(self, **filters) -> Optional[T]:
        """
        Obtiene el último registro que cumple los criterios.

        Args:
            **filters: Criterios de filtrado

        Returns:
            T | None: Última instancia encontrada o None
        """
        return self.model.objects.filter(**filters).last()

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    def update(self, pk: int, **kwargs) -> Optional[T]:
        """
        Actualiza una instancia por su ID.

        Args:
            pk: Primary key del objeto
            **kwargs: Campos a actualizar

        Returns:
            T | None: Instancia actualizada o None si no existe
        """
        try:
            instance = self.model.objects.get(pk=pk)
            for field, value in kwargs.items():
                setattr(instance, field, value)
            instance.save()
            logger.info(f"{self.model.__name__} con ID {pk} actualizado")
            return instance
        except ObjectDoesNotExist:
            logger.warning(
                f"{self.model.__name__} con ID {pk} no encontrado para actualizar"
            )
            return None
        except Exception as e:
            logger.error(f"Error al actualizar {self.model.__name__} con ID {pk}: {e}")
            raise

    def bulk_update(self, queryset: QuerySet[T], **kwargs) -> int:
        """
        Actualiza múltiples registros.

        Args:
            queryset: QuerySet de objetos a actualizar
            **kwargs: Campos a actualizar

        Returns:
            int: Número de registros actualizados
        """
        try:
            updated = queryset.update(**kwargs)
            logger.info(f"Actualizados {updated} registros de {self.model.__name__}")
            return updated
        except Exception as e:
            logger.error(f"Error en bulk_update de {self.model.__name__}: {e}")
            raise

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    def delete(self, pk: int) -> bool:
        """
        Elimina una instancia por su ID.

        Args:
            pk: Primary key del objeto

        Returns:
            bool: True si se eliminó, False si no existía
        """
        try:
            instance = self.model.objects.get(pk=pk)
            instance.delete()
            logger.info(f"{self.model.__name__} con ID {pk} eliminado")
            return True
        except ObjectDoesNotExist:
            logger.warning(
                f"{self.model.__name__} con ID {pk} no encontrado para eliminar"
            )
            return False
        except Exception as e:
            logger.error(f"Error al eliminar {self.model.__name__} con ID {pk}: {e}")
            raise

    def soft_delete(self, pk: int, field: str = "estado") -> bool:
        """
        Realiza un soft delete (desactivación) por ID.

        Args:
            pk: Primary key del objeto
            field: Campo booleano para marcar como eliminado

        Returns:
            bool: True si se desactivó, False si no existía
        """
        try:
            instance = self.model.objects.get(pk=pk)
            setattr(instance, field, False)
            instance.save()
            logger.info(f"{self.model.__name__} con ID {pk} desactivado (soft delete)")
            return True
        except ObjectDoesNotExist:
            logger.warning(
                f"{self.model.__name__} con ID {pk} no encontrado para soft delete"
            )
            return False

    def bulk_delete(self, **filters) -> int:
        """
        Elimina múltiples registros que cumplen los criterios.

        Args:
            **filters: Criterios de filtrado

        Returns:
            int: Número de registros eliminados
        """
        try:
            deleted, _ = self.model.objects.filter(**filters).delete()
            logger.info(f"Eliminados {deleted} registros de {self.model.__name__}")
            return deleted
        except Exception as e:
            logger.error(f"Error en bulk_delete de {self.model.__name__}: {e}")
            raise

    # =========================================================================
    # Transactional Operations
    # =========================================================================

    @transaction.atomic
    def create_with_transaction(self, **kwargs) -> T:
        """
        Crea una instancia dentro de una transacción.

        Args:
            **kwargs: Campos del modelo

        Returns:
            T: Instancia creada
        """
        return self.create(**kwargs)

    @transaction.atomic
    def update_with_transaction(self, pk: int, **kwargs) -> Optional[T]:
        """
        Actualiza una instancia dentro de una transacción.

        Args:
            pk: Primary key del objeto
            **kwargs: Campos a actualizar

        Returns:
            T | None: Instancia actualizada o None
        """
        return self.update(pk, **kwargs)

    # =========================================================================
    # Pagination
    # =========================================================================

    def get_paginated(
        self, page: int = 1, page_size: int = 10, **filters
    ) -> Dict[str, Any]:
        """
        Obtiene registros paginados.

        Args:
            page: Número de página (1-indexed)
            page_size: Tamaño de página
            **filters: Criterios de filtrado

        Returns:
            dict: Diccionario con datos paginados
        """
        queryset = self.get_by_filter(**filters) if filters else self.get_all()
        total = queryset.count()

        start = (page - 1) * page_size
        end = start + page_size

        items = list(queryset[start:end])

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": end < total,
            "has_previous": page > 1,
        }

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search(self, search_fields: List[str], search_term: str) -> QuerySet[T]:
        """
        Busca registros por término en múltiples campos.

        Args:
            search_fields: Lista de campos donde buscar
            search_term: Término de búsqueda

        Returns:
            QuerySet[T]: QuerySet con resultados
        """
        if not search_term:
            return self.get_all()

        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_term})

        return self.model.objects.filter(q_objects)
