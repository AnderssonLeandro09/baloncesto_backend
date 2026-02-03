import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Serializador para el login."""

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "El correo electrónico es requerido.",
            "blank": "El correo electrónico no puede estar vacío.",
            "invalid": "Ingrese un correo electrónico válido (debe contener @).",
        },
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        error_messages={
            "required": "La contraseña es requerida.",
            "blank": "La contraseña no puede estar vacía.",
        },
    )

    def validate_email(self, value):
        """Validación adicional del formato de correo electrónico."""
        if not value:
            raise serializers.ValidationError("El correo electrónico es requerido.")

        # Validar que contenga @ y tenga formato válido
        try:
            validate_email(value)
            # Asegurar que el dominio tenga un punto (comportamiento original del regex)
            if '.' not in value.split('@')[1]:
                raise DjangoValidationError("El dominio debe contener un punto.")
        except (DjangoValidationError, IndexError):
            raise serializers.ValidationError(
                "Ingrese un correo electrónico válido (debe contener @)."
            )

        return value.lower().strip()

    def validate_password(self, value):
        """Validación de la contraseña."""
        if not value:
            raise serializers.ValidationError("La contraseña es requerida.")

        if len(value.strip()) == 0:
            raise serializers.ValidationError("La contraseña no puede estar vacía.")

        return value
