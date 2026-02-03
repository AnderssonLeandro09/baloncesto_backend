"""Constantes de mensajes para la aplicación Basketball."""

from typing import Final


class ErrorMessages:
    """Mensajes de error estandarizados."""

    # Errores generales
    INTERNAL_SERVER_ERROR: Final[str] = "Error interno del servidor"
    INVALID_INPUT_DATA: Final[str] = "Datos de entrada inválidos"
    INVALID_ID: Final[str] = "ID inválido"
    UNAUTHORIZED: Final[str] = "No autorizado"

    # Errores de entrenador
    ENTRENADOR_NOT_FOUND: Final[str] = "Entrenador no encontrado"
    ENTRENADOR_ALREADY_EXISTS: Final[str] = "Ya existe un entrenador con ese external"
    ENTRENADOR_PERSONA_DATA_REQUIRED: Final[str] = "Datos de persona son obligatorios"
    ENTRENADOR_ESPECIALIDAD_REQUIRED: Final[
        str
    ] = "especialidad y club_asignado son obligatorios"
    ENTRENADOR_EMAIL_REQUIRED: Final[str] = "Email es obligatorio"
    ENTRENADOR_PASSWORD_REQUIRED: Final[str] = "Password es obligatorio"
    ENTRENADOR_EXTERNAL_NOT_RETURNED: Final[
        str
    ] = "El módulo de usuarios no retornó external_id"
    ENTRENADOR_EXTERNAL_IN_USE: Final[
        str
    ] = "El external_id retornado ya está en uso por otro entrenador"

    # Errores de prueba antropométrica
    PRUEBA_ANTROPOMETRICA_NOT_FOUND: Final[str] = "Prueba antropométrica no encontrada"
    NO_PERMISSION_TO_MODIFY: Final[str] = "No tiene permiso para modificar esta prueba"

    # Errores de prueba física
    PRUEBA_FISICA_NOT_FOUND: Final[str] = "Prueba física no encontrada"
    NO_PERMISSION_TO_REGISTER: Final[
        str
    ] = "No tiene permiso para registrar pruebas a este atleta"

    # Errores de atleta
    ATLETA_NOT_FOUND: Final[str] = "El atleta no existe"
    ATLETA_NO_ACTIVE_INSCRIPTION: Final[
        str
    ] = "El atleta no tiene inscripción habilitada"


class SuccessMessages:
    """Mensajes de éxito estandarizados."""

    CREATED_SUCCESSFULLY: Final[str] = "Creado exitosamente"
    UPDATED_SUCCESSFULLY: Final[str] = "Actualizado exitosamente"
    DELETED_SUCCESSFULLY: Final[str] = "Eliminado exitosamente"
    OPERATION_SUCCESSFUL: Final[str] = "Operación exitosa"


class ValidationMessages:
    """Mensajes de validación estandarizados."""

    REQUIRED_FIELD: Final[str] = "Este campo es requerido"
    INVALID_FORMAT: Final[str] = "Formato inválido"
    VALUE_TOO_LOW: Final[str] = "El valor es demasiado bajo"
    VALUE_TOO_HIGH: Final[str] = "El valor es demasiado alto"
    INVALID_DATE_RANGE: Final[str] = "Rango de fechas inválido"
