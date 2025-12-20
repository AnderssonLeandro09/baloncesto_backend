"""Permisos basados en rol usando el token emitido por el módulo de usuarios.

El rol se obtiene en este orden:
1. Header `X-Role` o `Role` enviado por el frontend.
2. Payload del token Bearer (sin validar firma, solo lectura del payload).
"""

import jwt
import logging
import os
from typing import Optional
from rest_framework import permissions

logger = logging.getLogger(__name__)


def _normalize_role(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).upper()
    if 'ADMIN' in normalized:
        return 'ADMIN'
    if 'DOCENTE' in normalized or 'ENTRENADOR' in normalized:
        return 'ENTRENADOR'
    if 'ESTUDIANT' in normalized:
        return 'ESTUDIANTE_VINCULACION'
    return normalized


class BaseRolePermission(permissions.BasePermission):
    """Permiso base que valida rol contra la lista `allowed_roles`."""

    allowed_roles: list[str] = []

    def _is_allowed(self, role_value: Optional[str]) -> bool:
        role = _normalize_role(role_value)
        return bool(role and role in self.allowed_roles)

    def _from_header(self, request):
        # SEGURIDAD: No confiar en headers manipulables por el cliente.
        # return request.headers.get('X-Role') or request.headers.get('Role')
        return None

    def _from_bearer(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        # Solo intentar decodificar si parece un JWT
        if token.count('.') != 2:
            return None

        try:
            payload = jwt.decode(
                token,
                os.getenv('USER_MODULE_JWT_SECRET', '1234567FDUCAMETB'),
                algorithms=['HS256'],
                options={'verify_signature': True},
            )
            return payload.get('role') or payload.get('stament') or payload.get('type_stament')
        except Exception as exc:  # pragma: no cover - logging auxiliar
            logger.debug("No se pudo leer el rol desde el token externo: %s", exc)
            return None

    def has_permission(self, request, view):
        header_role = self._from_header(request)
        if self._is_allowed(header_role):
            return True

        bearer_role = self._from_bearer(request)
        if self._is_allowed(bearer_role):
            return True

        return False


class IsAdmin(BaseRolePermission):
    allowed_roles = ['ADMIN']


class IsEntrenador(BaseRolePermission):
    allowed_roles = ['ENTRENADOR']


class IsEstudianteVinculacion(BaseRolePermission):
    allowed_roles = ['ESTUDIANTE_VINCULACION']


class IsAdminOrEntrenador(BaseRolePermission):
    allowed_roles = ['ADMIN', 'ENTRENADOR']


class IsAdminOrEntrenadorOrEstudiante(BaseRolePermission):
    allowed_roles = ['ADMIN', 'ENTRENADOR', 'ESTUDIANTE_VINCULACION']
