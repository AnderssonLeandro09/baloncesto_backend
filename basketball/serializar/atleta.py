from rest_framework import serializers
from ..models import Atleta, Inscripcion
from .persona import PersonaSerializer

class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = "__all__"

class AtletaDataSerializer(serializers.ModelSerializer):
    """Datos específicos del atleta para input."""
    class Meta:
        model = Atleta
        exclude = ["persona_external", "grupos"]

class InscripcionDataSerializer(serializers.ModelSerializer):
    """Datos específicos de la inscripción para input."""
    class Meta:
        model = Inscripcion
        fields = ["fecha_inscripcion", "tipo_inscripcion"]

class AtletaInscripcionInputSerializer(serializers.Serializer):
    """Input para crear/editar atleta + persona + inscripcion."""
    persona = PersonaSerializer()
    atleta = AtletaDataSerializer()
    inscripcion = InscripcionDataSerializer()

class AtletaInscripcionResponseSerializer(serializers.Serializer):
    """Respuesta con datos del atleta, la persona y la inscripción."""
    atleta = serializers.DictField()
    inscripcion = serializers.DictField()
    persona = serializers.DictField(allow_null=True)
