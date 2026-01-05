"""Permisos basados en rol usando JWT local."""

import jwt
import logging
from typing import Optional
from django.conf import settings
from rest_framework import permissions

logger = logging.getLogger(__name__)


def _normalize_role(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).upper()
    if "ADMIN" in normalized:
        return "ADMIN"
    if "DOCENTE" in normalized or "ENTRENADOR" in normalized:
        return "ENTRENADOR"
    if "ESTUDIANT" in normalized:
        return "ESTUDIANTE_VINCULACION"
    return normalized


class BaseRolePermission(permissions.BasePermission):
    """Permiso base que valida rol contra la lista `allowed_roles`."""

    allowed_roles: list[str] = []

    def _is_allowed(self, role_value: Optional[str]) -> bool:
        role = _normalize_role(role_value)
        return bool(role and role in self.allowed_roles)

    def _from_bearer(self, request):
        # Si ya pasó por JWTAuthentication, request.user tendrá el rol
        if hasattr(request.user, "role"):
            return request.user.role

        # Fallback por si acaso
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # Validamos usando NUESTRA SECRET_KEY local
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_signature": True},
            )
            return payload.get("role")
        except Exception as exc:
            logger.debug("Token inválido o expirado: %s", exc)
            return None

    def has_permission(self, request, view):
        bearer_role = self._from_bearer(request)
        if self._is_allowed(bearer_role):
            return True

        return False


class IsAdmin(BaseRolePermission):
    allowed_roles = ["ADMIN"]


class IsEntrenador(BaseRolePermission):
    allowed_roles = ["ENTRENADOR"]


class IsEstudianteVinculacion(BaseRolePermission):
    allowed_roles = ["ESTUDIANTE_VINCULACION"]


class IsAdminOrEntrenador(BaseRolePermission):
    allowed_roles = ["ADMIN", "ENTRENADOR"]


class IsAdminOrEntrenadorOrEstudiante(BaseRolePermission):
    allowed_roles = ["ADMIN", "ENTRENADOR", "ESTUDIANTE_VINCULACION"]


class IsEntrenadorOrEstudianteVinculacion(BaseRolePermission):
    allowed_roles = ["ENTRENADOR", "ESTUDIANTE_VINCULACION"]
