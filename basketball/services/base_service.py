"""
Servicio base para la capa de servicios del módulo Basketball

Implementación de BaseService y ServiceResult
"""

from typing import TypeVar, Generic, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ResultStatus(Enum):
    """Estados posibles de un resultado de servicio"""

    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"


@dataclass
class ServiceResult:
    """
    Resultado de una operación de servicio.

    Attributes:
        status: Estado del resultado
        data: Datos devueltos (si es exitoso)
        message: Mensaje descriptivo
        errors: Lista de errores (si hay)
    """

    status: ResultStatus
    data: Any = None
    message: str = ""
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def is_success(self) -> bool:
        """Verifica si el resultado es exitoso"""
        return self.status == ResultStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Verifica si hay error"""
        return self.status in (
            ResultStatus.ERROR,
            ResultStatus.VALIDATION_ERROR,
            ResultStatus.CONFLICT,
        )

    @classmethod
    def success(
        cls, data: Any = None, message: str = "Operación exitosa"
    ) -> "ServiceResult":
        """Crea un resultado exitoso"""
        return cls(status=ResultStatus.SUCCESS, data=data, message=message)

    @classmethod
    def error(cls, message: str, errors: List[str] = None) -> "ServiceResult":
        """Crea un resultado de error"""
        return cls(status=ResultStatus.ERROR, message=message, errors=errors or [])

    @classmethod
    def validation_error(
        cls, message: str, errors: List[str] = None
    ) -> "ServiceResult":
        """Crea un resultado de error de validación"""
        return cls(
            status=ResultStatus.VALIDATION_ERROR, message=message, errors=errors or []
        )

    @classmethod
    def not_found(cls, message: str = "Recurso no encontrado") -> "ServiceResult":
        """Crea un resultado de no encontrado"""
        return cls(status=ResultStatus.NOT_FOUND, message=message)

    @classmethod
    def conflict(cls, message: str, errors: List[str] = None) -> "ServiceResult":
        """Crea un resultado de conflicto"""
        return cls(status=ResultStatus.CONFLICT, message=message, errors=errors or [])

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        result = {
            "status": self.status.value,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.errors:
            result["errors"] = self.errors
        return result


T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Servicio base que define la interfaz común para todos los servicios.

    Proporciona métodos base para operaciones CRUD y validaciones.
    """

    dao = None

    def __init__(self):
        if self.dao is None:
            raise ValueError("Debe especificar el DAO en la clase hija")

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """
        Valida que los campos requeridos estén presentes.

        Args:
            data: Diccionario con los datos
            required_fields: Lista de campos requeridos

        Returns:
            List[str]: Lista de errores de validación
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"El campo '{field}' es requerido")
        return errors
