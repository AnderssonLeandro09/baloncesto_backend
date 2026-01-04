from rest_framework import serializers

class PersonaSerializer(serializers.Serializer):
    """
    Datos de la persona en el microservicio de usuarios.
    MODO FAIL-SAFE: Todos los campos excepto identification son opcionales.
    """

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación"
    )

    first_name = serializers.CharField(required=True) 
    last_name = serializers.CharField(required=True)

    # Usamos CharField y required=False para que no valide formato ni existencia obligatoria
    email = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    password = serializers.CharField(
        required=False, write_only=True, allow_null=True, allow_blank=True
    )
    
    phono = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, help_text="Teléfono/Celular"
    )
    
    gender = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    direction = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    type_identification = serializers.CharField(required=False, default="CEDULA")
    type_stament = serializers.CharField(required=False, default="ESTUDIANTES")