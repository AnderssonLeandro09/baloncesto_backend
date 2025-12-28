from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Serializador para el login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
