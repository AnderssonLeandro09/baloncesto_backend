"""
Servicio para Entrenador

Implementa la lógica de negocio, validaciones y manejo de errores
para la entidad `Entrenador`.
"""
from typing import Dict, Any, Optional, List
import re
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from basketball.services.base_service import BaseService, ServiceResult
from basketball.dao.model_daos import EntrenadorDAO
from basketball.models import Entrenador


class EntrenadorService(BaseService[Entrenador]):
    """
    Servicio para gestionar entrenadores.
    """

    REQUIRED_FIELDS = ['nombre', 'apellido', 'email', 'dni', 'clave', 'especialidad', 'club_asignado']
    UPDATE_FIELDS = ['nombre', 'apellido', 'email', 'especialidad', 'club_asignado', 'foto_perfil']

    def __init__(self):
        self.dao = EntrenadorDAO()

    def _validate_email_institucional(self, email: str) -> Optional[str]:
        if not email:
            return "El correo es obligatorio"
        email = email.strip().lower()
        if not email.endswith('@unl.edu.ec'):
            return "El correo debe ser institucional (@unl.edu.ec)"
        pattern = r'^[a-zA-Z0-9._%+-]+@unl\.edu\.ec$'
        if not re.match(pattern, email):
            return "Formato de correo inválido"
        return None

    def _validate_dni(self, dni: str) -> Optional[str]:
        if not dni:
            return "El DNI es obligatorio"
        if len(dni) != 10 or not dni.isdigit():
            return "El DNI debe tener 10 dígitos numéricos"
        return None

    def crear_entrenador(self, data: Dict[str, Any]) -> ServiceResult:
        errors: List[str] = []

        required_errors = self.validate_required_fields(data, self.REQUIRED_FIELDS)
        errors.extend(required_errors)
        if errors:
            return ServiceResult.validation_error("Error de validación", errors)

        email = data.get('email', '').lower().strip()
        dni = data.get('dni', '').strip()

        email_err = self._validate_email_institucional(email)
        if email_err:
            errors.append(email_err)

        dni_err = self._validate_dni(dni)
        if dni_err:
            errors.append(dni_err)

        if errors:
            return ServiceResult.validation_error("Error de validación", errors)

        # unicidad
        if self.dao.email_exists(email):
            return ServiceResult.conflict("El correo ya está registrado")
        if self.dao.dni_exists(dni):
            return ServiceResult.conflict("El DNI ya está registrado")

        try:
            entrenador = self.dao.create(
                nombre=data.get('nombre').strip(),
                apellido=data.get('apellido').strip(),
                email=email,
                dni=dni,
                clave=data.get('clave'),
                foto_perfil=data.get('foto_perfil'),
                rol='ENTRENADOR',
                especialidad=data.get('especialidad').strip(),
                club_asignado=data.get('club_asignado').strip()
            )

            return ServiceResult.success(data=self._entrenador_to_dict(entrenador), message="Entrenador creado exitosamente")

        except ValidationError as e:
            return ServiceResult.validation_error("Error de validación al crear entrenador", [str(e)])
        except IntegrityError as e:
            return ServiceResult.error("Error de integridad al crear entrenador", [str(e)])
        except Exception as e:
            return ServiceResult.error("Error inesperado al crear entrenador", [str(e)])

    def obtener_entrenador(self, pk: int) -> ServiceResult:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return ServiceResult.not_found("Entrenador no encontrado")
        return ServiceResult.success(data=self._entrenador_to_dict(entrenador), message="Entrenador encontrado")

    def listar_entrenadores(self, solo_activos: bool = True) -> ServiceResult:
        if solo_activos:
            entrenadores = self.dao.get_activos()
        else:
            entrenadores = self.dao.get_all()

        data = [self._entrenador_to_dict(e) for e in entrenadores]
        return ServiceResult.success(data=data, message=f"Se encontraron {len(data)} entrenadores")

    def actualizar_entrenador(self, pk: int, data: Dict[str, Any]) -> ServiceResult:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return ServiceResult.not_found("Entrenador no encontrado")

        errors: List[str] = []
        update_data: Dict[str, Any] = {}

        for field in self.UPDATE_FIELDS:
            if field in data:
                update_data[field] = data[field]

        if 'email' in update_data:
            email = update_data['email'].lower().strip()
            email_err = self._validate_email_institucional(email)
            if email_err:
                errors.append(email_err)
            elif self.dao.email_exists(email, exclude_pk=pk):
                errors.append('El correo ya está en uso')
            else:
                update_data['email'] = email

        if 'semestre' in update_data:
            # campo no aplicable a entrenador, ignorado por seguridad
            update_data.pop('semestre', None)

        if errors:
            return ServiceResult.validation_error("Error de validación", errors)

        try:
            actualizado = self.dao.update(pk, **update_data)
            if not actualizado:
                return ServiceResult.not_found("Entrenador no encontrado para actualizar")
            return ServiceResult.success(data=self._entrenador_to_dict(actualizado), message="Entrenador actualizado")
        except ValidationError as e:
            return ServiceResult.validation_error("Error de validación", [str(e)])
        except Exception as e:
            return ServiceResult.error("Error inesperado al actualizar entrenador", [str(e)])

    def dar_de_baja(self, pk: int) -> ServiceResult:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return ServiceResult.not_found("Entrenador no encontrado")
        if not entrenador.estado:
            return ServiceResult.conflict("El entrenador ya está dado de baja")

        success = self.dao.soft_delete(pk, field='estado')
        if success:
            return ServiceResult.success(message="Entrenador dado de baja")
        return ServiceResult.error("No se pudo dar de baja al entrenador")

    def reactivar_entrenador(self, pk: int) -> ServiceResult:
        entrenador = self.dao.get_by_id(pk)
        if not entrenador:
            return ServiceResult.not_found("Entrenador no encontrado")
        if entrenador.estado:
            return ServiceResult.conflict("El entrenador ya está activo")

        try:
            actualizado = self.dao.update(pk, estado=True)
            if actualizado:
                return ServiceResult.success(message="Entrenador reactivado")
            return ServiceResult.error("No se pudo reactivar el entrenador")
        except Exception as e:
            return ServiceResult.error("Error inesperado al reactivar entrenador", [str(e)])

    def buscar_entrenadores(self, termino: str) -> ServiceResult:
        resultados = self.dao.search_entrenadores(termino)
        data = [self._entrenador_to_dict(e) for e in resultados]
        return ServiceResult.success(data=data, message=f"Se encontraron {len(data)} entrenadores")

    def _entrenador_to_dict(self, entrenador: Entrenador) -> Dict[str, Any]:
        return {
            'id': entrenador.pk,
            'nombre': entrenador.nombre,
            'apellido': entrenador.apellido,
            'email': entrenador.email,
            'dni': entrenador.dni,
            'foto_perfil': entrenador.foto_perfil,
            'rol': getattr(entrenador, 'rol', 'ENTRENADOR'),
            'estado': entrenador.estado,
            'fecha_registro': entrenador.fecha_registro.isoformat() if getattr(entrenador, 'fecha_registro', None) else None,
            'especialidad': getattr(entrenador, 'especialidad', None),
            'club_asignado': getattr(entrenador, 'club_asignado', None),
        }
