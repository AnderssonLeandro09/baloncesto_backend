"""
Permisos personalizados para el módulo Basketball

Define permisos basados en roles y estados de usuario.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny


class IsAdmin(BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol de administrador.
    """
    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Verificar si es superusuario o staff
        return request.user.is_superuser or request.user.is_staff


class IsEntrenador(BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol de entrenador.
    """
    message = "Solo los entrenadores pueden realizar esta acción."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Verificar rol de entrenador (ajustar según tu modelo de usuario)
        return hasattr(request.user, 'rol') and request.user.rol == 'ENTRENADOR'


class IsEstudianteVinculacion(BasePermission):
    """
    Permiso que solo permite acceso a estudiantes de vinculación.
    """
    message = "Solo los estudiantes de vinculación pueden realizar esta acción."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'rol') and request.user.rol == 'ESTUDIANTE_VINCULACION'


class IsAdminOrReadOnly(BasePermission):
    """
    Permiso que permite lectura a todos los autenticados,
    pero solo escritura a administradores.
    """
    message = "Solo los administradores pueden modificar estos datos."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Métodos seguros (lectura) permitidos para todos los autenticados
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Métodos de escritura solo para administradores
        return request.user.is_superuser or request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    """
    Permiso que permite acceso al propietario del objeto o a administradores.
    Útil para que los usuarios solo puedan editar sus propios datos.
    """
    message = "Solo puedes modificar tus propios datos o ser administrador."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores tienen acceso total
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verificar si el usuario es el propietario
        # Ajustar según tu modelo (puede ser user_id, usuario, etc.)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'usuario'):
            return obj.usuario.id == request.user.id
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        
        return False


class CanManageAtletas(BasePermission):
    """
    Permiso para gestionar atletas.
    Administradores y entrenadores pueden gestionar atletas.
    """
    message = "Solo administradores y entrenadores pueden gestionar atletas."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores tienen acceso total
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Entrenadores pueden gestionar atletas
        if hasattr(request.user, 'rol') and request.user.rol == 'ENTRENADOR':
            return True
        
        return False


# =============================================================================
# Permisos compuestos (combinaciones)
# =============================================================================

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Permite lectura sin autenticación, pero requiere autenticación para escritura.
    Útil para endpoints públicos de consulta.
    """
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user and request.user.is_authenticated
