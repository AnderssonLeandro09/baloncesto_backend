"""
Serializers personalizados para JWT Authentication

Permite incluir información adicional del usuario en las respuestas de tokens.
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que incluye información adicional del usuario
    en el token JWT y en la respuesta.
    """

    @classmethod
    def get_token(cls, user):
        """
        Genera el token e incluye claims personalizados.
        """
        token = super().get_token(user)

        # Agregar claims personalizados al token
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        # Si el usuario tiene nombre completo
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            token['full_name'] = f"{user.first_name} {user.last_name}".strip()
        
        # Si el usuario tiene un rol personalizado
        if hasattr(user, 'rol'):
            token['rol'] = user.rol
        
        return token

    def validate(self, attrs):
        """
        Valida las credenciales y agrega información adicional a la respuesta.
        """
        data = super().validate(attrs)
        
        # Agregar información del usuario a la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
        }
        
        # Agregar rol si existe
        if hasattr(self.user, 'rol'):
            data['user']['rol'] = self.user.rol
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT con información adicional.
    """
    serializer_class = CustomTokenObtainPairSerializer
