import re
from rest_framework import serializers


class PersonaSerializer(serializers.Serializer):
    """
    Datos de la persona en el microservicio de usuarios.
    MODO FAIL-SAFE: Todos los campos excepto identification son opcionales.
    
    Validaciones:
    - first_name/last_name: Solo letras y espacios
    - identification: 10 dígitos numéricos (cédula ecuatoriana)
    - phono: 9-15 dígitos numéricos
    """

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación (10 dígitos)"
    )

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    # Usamos CharField y required=False para que no valide formato ni existencia obligatoria
    email = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    password = serializers.CharField(
        required=False, write_only=True, allow_null=True, allow_blank=True
    )

    phono = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, help_text="Teléfono/Celular (9-15 dígitos)"
    )

    gender = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    direction = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    type_identification = serializers.CharField(required=False, default="CEDULA")
    type_stament = serializers.CharField(required=False, default="ESTUDIANTES")

    # =========================================================================
    # VALIDACIONES PERSONALIZADAS
    # =========================================================================

    def validate_first_name(self, value):
        """
        Valida que el nombre solo contenga letras y espacios.
        Permite caracteres con tildes (á, é, í, ó, ú, ñ).
        """
        if not value:
            return value
        
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError("El nombre es requerido.")
        
        # Patrón: letras (incluyendo tildes), espacios y apóstrofes
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"
        
        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )
        
        # Capitalizar cada palabra
        return ' '.join(word.capitalize() for word in value.split())

    def validate_last_name(self, value):
        """
        Valida que el apellido solo contenga letras y espacios.
        Permite caracteres con tildes (á, é, í, ó, ú, ñ).
        """
        if not value:
            return value
        
        value = value.strip()
        
        if not value:
            raise serializers.ValidationError("El apellido es requerido.")
        
        # Patrón: letras (incluyendo tildes), espacios y apóstrofes
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"
        
        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El apellido solo puede contener letras y espacios."
            )
        
        # Capitalizar cada palabra
        return ' '.join(word.capitalize() for word in value.split())

    def validate_identification(self, value):
        """
        Valida la cédula ecuatoriana:
        - Debe contener exactamente 10 dígitos numéricos
        - No puede estar vacía
        """
        if not value:
            raise serializers.ValidationError("La cédula es requerida.")
        
        value = value.strip()
        
        # Remover espacios o guiones que el usuario pueda haber ingresado
        value = re.sub(r'[\s\-]', '', value)
        
        if not value.isdigit():
            raise serializers.ValidationError(
                "La cédula debe contener solo dígitos numéricos."
            )
        
        if len(value) != 10:
            raise serializers.ValidationError(
                "La cédula debe tener exactamente 10 dígitos."
            )
        
        return value

    def validate_phono(self, value):
        """
        Valida el número de teléfono:
        - Solo dígitos numéricos
        - Longitud entre 9 y 15 caracteres
        """
        if not value:
            return value
        
        value = value.strip()
        
        if not value:
            return value
        
        # Remover espacios, guiones y paréntesis comunes en teléfonos
        value = re.sub(r'[\s\-\(\)\+]', '', value)
        
        if not value.isdigit():
            raise serializers.ValidationError(
                "El teléfono debe contener solo dígitos numéricos."
            )
        
        if len(value) < 9 or len(value) > 15:
            raise serializers.ValidationError(
                "El teléfono debe tener entre 9 y 15 dígitos."
            )
        
        return value


class PersonaMinimalSerializer(serializers.Serializer):
    """
    Serializer mínimo para datos de persona.
    Solo contiene los campos esenciales.
    """

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación"
    )
    first_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
