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

    def create_grupo(self, data: Dict[str, Any]) -> GrupoAtleta:
        """Crea un nuevo grupo de atletas y asigna atletas si se proporcionan."""
        with transaction.atomic():
            self._validate_rango_edad(
                data.get("rango_edad_minima"), data.get("rango_edad_maxima")
            )
            
            entrenador_id = data.get("entrenador")
            if not entrenador_id:
                raise ValidationError("El entrenador es obligatorio")
                
            if not Entrenador.objects.filter(id=entrenador_id).exists():
                raise ValidationError("El entrenador especificado no existe")

            atleta_ids = data.pop("atletas", [])
            
            # Ajustar para usar entrenador_id en lugar de la instancia
            if "entrenador" in data:
                data["entrenador_id"] = data.pop("entrenador")

            grupo = self.dao.create(**data)

            if atleta_ids:
                self._assign_atletas(grupo, atleta_ids)

            return grupo

    def update_grupo(self, pk: int, data: Dict[str, Any]) -> Optional[GrupoAtleta]:
        """Actualiza un grupo existente y sus atletas."""
        with transaction.atomic():
            grupo = self.dao.get_by_id_activo(pk)
            if not grupo:
                return None

            min_edad = data.get("rango_edad_minima", grupo.rango_edad_minima)
            max_edad = data.get("rango_edad_maxima", grupo.rango_edad_maxima)
            self._validate_rango_edad(min_edad, max_edad)

            entrenador_id = data.get("entrenador")
            if entrenador_id and not Entrenador.objects.filter(id=entrenador_id).exists():
                raise ValidationError("El entrenador especificado no existe")

            atleta_ids = data.pop("atletas", None)
            
            # Ajustar para usar entrenador_id en lugar de la instancia
            if "entrenador" in data:
                data["entrenador_id"] = data.pop("entrenador")

            updated_grupo = self.dao.update(pk, **data)

            if atleta_ids is not None:
                self._assign_atletas(updated_grupo, atleta_ids)

            return updated_grupo

    def _assign_atletas(self, grupo: GrupoAtleta, atleta_ids: List[int]):
        """Asocia una lista de atletas al grupo, validando que existan."""
        # SECURITY: Limitar cantidad de atletas para prevenir DoS
        if len(atleta_ids) > 100:
            raise ValidationError("No se pueden asignar más de 100 atletas a un grupo")
        
        # SECURITY: Validar que todos los IDs sean positivos
        if any(aid <= 0 for aid in atleta_ids):
            raise ValidationError("Los IDs de atletas deben ser números positivos")
        
        atletas = Atleta.objects.filter(id__in=atleta_ids)
        if len(atletas) != len(atleta_ids):
            found_ids = set(atletas.values_list("id", flat=True))
            missing_ids = set(atleta_ids) - found_ids
            raise ValidationError(f"Los siguientes IDs de atletas no existen: {list(missing_ids)}")
        
        # Validar que los atletas cumplan con el rango de edad del grupo
        for atleta in atletas:
            if atleta.edad < grupo.rango_edad_minima or atleta.edad > grupo.rango_edad_maxima:
                raise ValidationError(
                    f"El atleta con ID {atleta.id} (edad: {atleta.edad}) "
                    f"no cumple con el rango de edad del grupo ({grupo.rango_edad_minima}-{grupo.rango_edad_maxima})"
                )

        grupo.atletas.set(atletas)

    def list_atletas_elegibles(self, grupo_id: Optional[int] = None, min_edad: Optional[int] = None, max_edad: Optional[int] = None) -> List[Atleta]:
        """Lista atletas que cumplen con el rango de edad de un grupo o rango específico."""
        if grupo_id:
            grupo = self.dao.get_by_id_activo(grupo_id)
            if not grupo:
                raise ValidationError("Grupo no encontrado")
            min_edad = grupo.rango_edad_minima
            max_edad = grupo.rango_edad_maxima
        
        if min_edad is None or max_edad is None:
            raise ValidationError("Se requiere un grupo_id o un rango de edad (min_edad, max_edad)")

        queryset = Atleta.objects.filter(
            edad__gte=min_edad, 
            edad__lte=max_edad
        )
        
        if grupo_id:
            queryset = queryset.exclude(grupos__id=grupo_id)
            
        return list(queryset)

    def delete_grupo(self, pk: int) -> bool:
        """Realiza una baja lógica del grupo."""
        updated = self.dao.update(pk, eliminado=True)
        return updated is not None

    def get_grupo(self, pk: int) -> Optional[GrupoAtleta]:
        """Obtiene un grupo por su ID."""
        return self.dao.get_by_id_activo(pk)

    def list_grupos(self) -> List[GrupoAtleta]:
        """Lista todos los grupos activos."""
        return list(self.dao.get_activos())

    def list_grupos_por_entrenador(self, entrenador_id: int) -> List[GrupoAtleta]:
        """Lista los grupos activos de un entrenador."""
        return list(self.dao.get_by_entrenador(entrenador_id))

    def _validate_rango_edad(self, minima: Any, maxima: Any):
        """Valida que el rango de edad sea coherente."""
        if minima is not None and maxima is not None:
            min_edad = int(minima)
            max_edad = int(maxima)
            
            if min_edad > max_edad:
                raise ValidationError("La edad mínima no puede ser mayor a la máxima")
            if min_edad < 0:
                raise ValidationError("La edad mínima no puede ser negativa")
            # SECURITY: Validar límites razonables de edad
            if max_edad > 150:
                raise ValidationError("La edad máxima no puede ser mayor a 150")
            if max_edad < min_edad:
                raise ValidationError("El rango de edad no es válido")
