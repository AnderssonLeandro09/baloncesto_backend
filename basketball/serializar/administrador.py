from rest_framework import serializers
from ..models import Administrador
from .persona import PersonaSerializer

class AdministradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrador
        fields = '__all__'

class AdministradorDataSerializer(serializers.ModelSerializer):
    """Datos específicos del administrador."""
    class Meta:
        model = Administrador
        fields = ['cargo']

class AdministradorInputSerializer(serializers.Serializer):
    """Input para crear/editar administrador + persona."""
    persona = PersonaSerializer()
    administrador = AdministradorDataSerializer()

class AdministradorResponseSerializer(serializers.Serializer):
    """Respuesta con datos del administrador y la persona."""
    administrador = AdministradorSerializer()
    persona = serializers.DictField(allow_null=True)
