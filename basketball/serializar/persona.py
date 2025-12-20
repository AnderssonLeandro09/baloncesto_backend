from rest_framework import serializers

class PersonaSerializer(serializers.Serializer):
    """Datos de la persona en el microservicio de usuarios."""
    identification = serializers.CharField(required=True, help_text="Cédula o identificación")
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    phono = serializers.CharField(required=False, help_text="Teléfono/Celular")
    gender = serializers.CharField(required=False)
    direction = serializers.CharField(required=False)
    type_identification = serializers.CharField(required=False, default='CEDULA')
    type_stament = serializers.CharField(required=False, default='ESTUDIANTES')
