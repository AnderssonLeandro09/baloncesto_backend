from rest_framework import serializers
from ..models import Entrenador
from .persona import PersonaSerializer


class EntrenadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrenador
        fields = "__all__"


class EntrenadorDataSerializer(serializers.ModelSerializer):
    """Datos específicos del entrenador."""

    class Meta:
        model = Entrenador
        fields = ["especialidad", "club_asignado"]


class EntrenadorInputSerializer(serializers.Serializer):
    """Input para crear/editar entrenador + persona."""

    persona = PersonaSerializer()
    entrenador = EntrenadorDataSerializer()


class EntrenadorResponseSerializer(serializers.Serializer):
    """Respuesta con datos del entrenador y la persona."""

    entrenador = EntrenadorSerializer()
    persona = serializers.DictField(allow_null=True)