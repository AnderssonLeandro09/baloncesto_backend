"""
Servicio para el módulo de Estudiantes de Vinculación

Implementa la lógica de negocio y validaciones específicas
"""

import re
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from basketball.services.base_service import BaseService, ServiceResult
from basketball.dao.model_daos import EstudianteVinculacionDAO
from basketball.models import EstudianteVinculacion


class EstudianteVinculacionService(BaseService[EstudianteVinculacion]):
    """
    Servicio para gestionar estudiantes de vinculación.
    Implementa la lógica de negocio y validaciones específicas.
    """
    
    REQUIRED_FIELDS = ['nombre', 'apellido', 'email', 'dni', 'carrera', 'semestre', 'clave']
    UPDATE_FIELDS = ['nombre', 'apellido', 'email', 'carrera', 'semestre', 'foto_perfil']
    
    def __init__(self):
        self.dao = EstudianteVinculacionDAO()
    
    def _validate_email_institucional(self, email: str) -> Optional[str]:
        """
        Valida que el email sea institucional (@unl.edu.ec).
        
        Args:
            email: Email a validar
            
        Returns:
            str | None: Mensaje de error o None si es válido
        """
        if not email:
            return "El email es requerido"
        
        if not email.endswith('@unl.edu.ec'):
            return "El correo debe ser institucional (@unl.edu.ec)"
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@unl\.edu\.ec$'
        if not re.match(email_pattern, email):
            return "El formato del correo institucional no es válido"
        
        return None
    
    def _validate_dni(self, dni: str) -> Optional[str]:
        """
        Valida el formato del DNI.
        
        Args:
            dni: DNI a validar
            
        Returns:
            str | None: Mensaje de error o None si es válido
        """
        if not dni:
            return "El DNI es requerido"
        
        if len(dni) != 10 or not dni.isdigit():
            return "El DNI debe tener 10 dígitos numéricos"
        
        return None
    
    def _validate_semestre(self, semestre: str) -> Optional[str]:
        """
        Valida el semestre del estudiante.
        
        Args:
            semestre: Semestre a validar
            
        Returns:
            str | None: Mensaje de error o None si es válido
        """
        if not semestre:
            return "El semestre es requerido"
        
        # Validar que sea un semestre válido (1-10 o formato similar)
        valid_semestres = [str(i) for i in range(1, 11)]
        semestre_normalizado = semestre.replace('°', '').replace('vo', '').replace('mo', '').strip()
        
        if semestre_normalizado not in valid_semestres and semestre not in valid_semestres:
            return "El semestre debe ser un valor entre 1 y 10"
        
        return None
    
    def crear_estudiante(self, data: Dict[str, Any]) -> ServiceResult:
        """
        Crea un nuevo estudiante de vinculación.
        
        Args:
            data: Diccionario con los datos del estudiante
            
        Returns:
            ServiceResult: Resultado de la operación
        """
        errors = []
        
        # Validar campos requeridos
        required_errors = self.validate_required_fields(data, self.REQUIRED_FIELDS)
        errors.extend(required_errors)
        
        if errors:
            return ServiceResult.validation_error(
                "Error de validación en los campos requeridos",
                errors
            )
        
        # Normalizar email antes de validar
        email = data.get('email', '').lower().strip()
        
        # Validaciones específicas
        email_error = self._validate_email_institucional(email)
        if email_error:
            errors.append(email_error)
        
        dni_error = self._validate_dni(data.get('dni', ''))
        if dni_error:
            errors.append(dni_error)
        
        semestre_error = self._validate_semestre(data.get('semestre', ''))
        if semestre_error:
            errors.append(semestre_error)
        
        if errors:
            return ServiceResult.validation_error(
                "Error de validación",
                errors
            )
        
        # Verificar unicidad de email (usando email normalizado)
        if self.dao.email_exists(email):
            return ServiceResult.conflict(
                "El email ya está registrado",
                ["Ya existe un estudiante con este correo institucional"]
            )
        
        # Verificar unicidad de DNI
        if self.dao.dni_exists(data['dni']):
            return ServiceResult.conflict(
                "El DNI ya está registrado",
                ["Ya existe un estudiante con este DNI"]
            )
        
        # Crear el estudiante
        try:
            estudiante_data = {
                'nombre': data['nombre'].strip(),
                'apellido': data['apellido'].strip(),
                'email': email,  # Usar email normalizado
                'dni': data['dni'].strip(),
                'clave': data['clave'],  # TODO: Hash de contraseña cuando se integre JWT
                'carrera': data['carrera'].strip(),
                'semestre': data['semestre'].strip(),
                'rol': 'ESTUDIANTE_VINCULACION',
                'estado': True,
                'foto_perfil': data.get('foto_perfil', ''),
            }
            
            estudiante = self.dao.create(**estudiante_data)
            
            return ServiceResult.success(
                data=self._estudiante_to_dict(estudiante),
                message="Estudiante de vinculación creado exitosamente"
            )
        except ValidationError as e:
            return ServiceResult.validation_error(
                "Error de validación al crear el estudiante",
                list(e.messages) if hasattr(e, 'messages') else [str(e)]
            )
        except IntegrityError as e:
            return ServiceResult.conflict(
                "Error de integridad en los datos",
                [str(e)]
            )
        except Exception as e:
            return ServiceResult.error(
                "Error al crear el estudiante",
                [str(e)]
            )
    
    def obtener_estudiante(self, pk: int) -> ServiceResult:
        """
        Obtiene un estudiante por su ID.
        
        Args:
            pk: ID del estudiante
            
        Returns:
            ServiceResult: Resultado con el estudiante o error
        """
        estudiante = self.dao.get_by_id(pk)
        
        if not estudiante:
            return ServiceResult.not_found(
                f"Estudiante con ID {pk} no encontrado"
            )
        
        return ServiceResult.success(
            data=self._estudiante_to_dict(estudiante),
            message="Estudiante encontrado"
        )
    
    def obtener_estudiante_por_email(self, email: str) -> ServiceResult:
        """
        Obtiene un estudiante por su email.
        
        Args:
            email: Email del estudiante
            
        Returns:
            ServiceResult: Resultado con el estudiante o error
        """
        estudiante = self.dao.get_by_email(email)
        
        if not estudiante:
            return ServiceResult.not_found(
                f"Estudiante con email {email} no encontrado"
            )
        
        return ServiceResult.success(
            data=self._estudiante_to_dict(estudiante),
            message="Estudiante encontrado"
        )
    
    def listar_estudiantes(self, solo_activos: bool = True) -> ServiceResult:
        """
        Lista todos los estudiantes.
        
        Args:
            solo_activos: Si True, solo devuelve estudiantes activos
            
        Returns:
            ServiceResult: Resultado con la lista de estudiantes
        """
        if solo_activos:
            estudiantes = self.dao.get_activos()
        else:
            estudiantes = self.dao.get_all()
        
        data = [self._estudiante_to_dict(e) for e in estudiantes]
        
        return ServiceResult.success(
            data=data,
            message=f"Se encontraron {len(data)} estudiantes"
        )
    
    def listar_estudiantes_paginado(
        self, 
        page: int = 1, 
        page_size: int = 10,
        solo_activos: bool = True
    ) -> ServiceResult:
        """
        Lista estudiantes con paginación.
        
        Args:
            page: Número de página
            page_size: Tamaño de página
            solo_activos: Si True, solo devuelve estudiantes activos
            
        Returns:
            ServiceResult: Resultado con datos paginados
        """
        filters = {'estado': True} if solo_activos else {}
        
        paginated = self.dao.get_paginated(page, page_size, **filters)
        paginated['items'] = [self._estudiante_to_dict(e) for e in paginated['items']]
        
        return ServiceResult.success(
            data=paginated,
            message=f"Página {page} de {paginated['total_pages']}"
        )
    
    def actualizar_estudiante(self, pk: int, data: Dict[str, Any]) -> ServiceResult:
        """
        Actualiza un estudiante existente.
        
        Args:
            pk: ID del estudiante
            data: Datos a actualizar
            
        Returns:
            ServiceResult: Resultado de la operación
        """
        # Verificar que existe
        estudiante = self.dao.get_by_id(pk)
        if not estudiante:
            return ServiceResult.not_found(
                f"Estudiante con ID {pk} no encontrado"
            )
        
        errors = []
        update_data = {}
        
        # Filtrar solo campos permitidos para actualización
        for field in self.UPDATE_FIELDS:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return ServiceResult.validation_error(
                "No se proporcionaron datos para actualizar",
                ["Debe proporcionar al menos un campo para actualizar"]
            )
        
        # Validaciones específicas si se actualizan ciertos campos
        if 'email' in update_data:
            email_error = self._validate_email_institucional(update_data['email'])
            if email_error:
                errors.append(email_error)
            elif self.dao.email_exists(update_data['email'], exclude_pk=pk):
                return ServiceResult.conflict(
                    "El email ya está registrado",
                    ["Ya existe otro estudiante con este correo institucional"]
                )
            update_data['email'] = update_data['email'].lower().strip()
        
        if 'semestre' in update_data:
            semestre_error = self._validate_semestre(update_data['semestre'])
            if semestre_error:
                errors.append(semestre_error)
        
        if errors:
            return ServiceResult.validation_error(
                "Error de validación",
                errors
            )
        
        # Actualizar
        try:
            estudiante_actualizado = self.dao.update(pk, **update_data)
            
            return ServiceResult.success(
                data=self._estudiante_to_dict(estudiante_actualizado),
                message="Estudiante actualizado exitosamente"
            )
        except ValidationError as e:
            return ServiceResult.validation_error(
                "Error de validación al actualizar",
                list(e.messages) if hasattr(e, 'messages') else [str(e)]
            )
        except Exception as e:
            return ServiceResult.error(
                "Error al actualizar el estudiante",
                [str(e)]
            )
    
    def dar_de_baja(self, pk: int) -> ServiceResult:
        """
        Da de baja un estudiante (soft delete).
        
        Args:
            pk: ID del estudiante
            
        Returns:
            ServiceResult: Resultado de la operación
        """
        estudiante = self.dao.get_by_id(pk)
        if not estudiante:
            return ServiceResult.not_found(
                f"Estudiante con ID {pk} no encontrado"
            )
        
        if not estudiante.estado:
            return ServiceResult.validation_error(
                "El estudiante ya se encuentra dado de baja",
                ["El estudiante ya fue desactivado anteriormente"]
            )
        
        success = self.dao.soft_delete(pk, field='estado')
        
        if success:
            return ServiceResult.success(
                data={'id': pk, 'estado': False},
                message="Estudiante dado de baja exitosamente"
            )
        else:
            return ServiceResult.error(
                "Error al dar de baja al estudiante",
                ["No se pudo completar la operación"]
            )
    
    def reactivar_estudiante(self, pk: int) -> ServiceResult:
        """
        Reactiva un estudiante dado de baja.
        
        Args:
            pk: ID del estudiante
            
        Returns:
            ServiceResult: Resultado de la operación
        """
        estudiante = self.dao.get_by_id(pk)
        if not estudiante:
            return ServiceResult.not_found(
                f"Estudiante con ID {pk} no encontrado"
            )
        
        if estudiante.estado:
            return ServiceResult.validation_error(
                "El estudiante ya se encuentra activo",
                ["El estudiante no está dado de baja"]
            )
        
        estudiante_actualizado = self.dao.update(pk, estado=True)
        
        if estudiante_actualizado:
            return ServiceResult.success(
                data=self._estudiante_to_dict(estudiante_actualizado),
                message="Estudiante reactivado exitosamente"
            )
        else:
            return ServiceResult.error(
                "Error al reactivar al estudiante",
                ["No se pudo completar la operación"]
            )
    
    def buscar_estudiantes(self, termino: str) -> ServiceResult:
        """
        Busca estudiantes por término de búsqueda.
        
        Args:
            termino: Término de búsqueda
            
        Returns:
            ServiceResult: Resultado con estudiantes encontrados
        """
        if not termino or len(termino) < 2:
            return ServiceResult.validation_error(
                "Término de búsqueda inválido",
                ["El término debe tener al menos 2 caracteres"]
            )
        
        estudiantes = self.dao.search_estudiantes(termino)
        data = [self._estudiante_to_dict(e) for e in estudiantes]
        
        return ServiceResult.success(
            data=data,
            message=f"Se encontraron {len(data)} estudiantes"
        )
    
    def filtrar_por_carrera(self, carrera: str) -> ServiceResult:
        """
        Filtra estudiantes por carrera.
        
        Args:
            carrera: Nombre de la carrera
            
        Returns:
            ServiceResult: Resultado con estudiantes filtrados
        """
        estudiantes = self.dao.get_by_carrera(carrera)
        data = [self._estudiante_to_dict(e) for e in estudiantes]
        
        return ServiceResult.success(
            data=data,
            message=f"Se encontraron {len(data)} estudiantes en la carrera"
        )
    
    def _estudiante_to_dict(self, estudiante: EstudianteVinculacion) -> Dict[str, Any]:
        """
        Convierte un estudiante a diccionario.
        
        Args:
            estudiante: Instancia del estudiante
            
        Returns:
            Dict: Representación en diccionario
        """
        return {
            'id': estudiante.pk,
            'nombre': estudiante.nombre,
            'apellido': estudiante.apellido,
            'email': estudiante.email,
            'dni': estudiante.dni,
            'foto_perfil': estudiante.foto_perfil,
            'rol': estudiante.rol,
            'estado': estudiante.estado,
            'fecha_registro': estudiante.fecha_registro.isoformat() if estudiante.fecha_registro else None,
            'carrera': estudiante.carrera,
            'semestre': estudiante.semestre,
        }
