from rest_framework import serializers


class PersonaSerializer(serializers.Serializer):
    """Datos de la persona en el microservicio de usuarios."""

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación"
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, write_only=True, allow_blank=True)
    phono = serializers.CharField(required=False, help_text="Teléfono/Celular")
    gender = serializers.CharField(required=False)
    direction = serializers.CharField(required=False)
    type_identification = serializers.CharField(required=False, default="CEDULA")
    type_stament = serializers.CharField(required=False, default="ESTUDIANTES")


class PersonaMinimalSerializer(serializers.Serializer):
    """Datos mínimos de la persona (nombre, apellido, identificación)."""

    nombre = serializers.CharField(source="first_name", read_only=True)
    apellido = serializers.CharField(source="last_name", read_only=True)
    identificacion = serializers.CharField(source="identification", read_only=True)
