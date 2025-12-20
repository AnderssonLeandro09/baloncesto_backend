from rest_framework import serializers
from ..models import EstudianteVinculacion
from .persona import PersonaSerializer

class EstudianteVinculacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudianteVinculacion
        fields = '__all__'

class EstudianteVinculacionDataSerializer(serializers.ModelSerializer):
    """Datos específicos del estudiante de vinculación."""
    class Meta:
        model = EstudianteVinculacion
        fields = ['carrera', 'semestre']

class EstudianteVinculacionInputSerializer(serializers.Serializer):
    """Input para crear/editar estudiante de vinculación + persona."""
    persona = PersonaSerializer()
    estudiante = EstudianteVinculacionDataSerializer()

class EstudianteVinculacionResponseSerializer(serializers.Serializer):
    """Respuesta con datos del estudiante y la persona."""
    estudiante = EstudianteVinculacionSerializer()
    persona = serializers.DictField(allow_null=True)
