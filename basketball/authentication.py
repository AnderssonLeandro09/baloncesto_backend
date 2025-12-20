"""Autenticación personalizada para JWT local."""

import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Administrador, Entrenador, EstudianteVinculacion

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('El token ha expirado')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token inválido')

        user_id = payload.get('sub')
        role = payload.get('role')
        
        if not user_id:
            raise AuthenticationFailed('Token sin ID de usuario')

        # Crear un objeto usuario simple (o buscar en BD si fuera User de Django)
        # Como no usamos el modelo User de Django por defecto, retornamos un objeto simple
        # o None para el usuario y None para el auth.
        # DRF espera (user, auth).
        
        return (AuthenticatedUser(user_id, role, payload), token)

class AuthenticatedUser:
    """Usuario temporal para request.user"""
    def __init__(self, pk, role, payload):
        self.pk = pk
        self.role = role
        self.payload = payload
        self.is_authenticated = True
        self.email = payload.get('email')
        self.name = payload.get('name')

    def __str__(self):
        return f"{self.name} ({self.role})"
