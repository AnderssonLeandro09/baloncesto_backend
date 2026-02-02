from rest_framework import serializers
from ..models import Entrenador
from .persona import PersonaSerializer


class EntrenadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrenador
        fields = "__all__"


class EntrenadorDataSerializer(serializers.ModelSerializer):
    """Datos específicos del entrenador."""

    def validate_especialidad(self, value):
        """Valida que especialidad no esté vacía y no sea solo espacios."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "La especialidad es requerida y no puede estar vacía"
            )
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "La especialidad debe tener al menos 3 caracteres"
            )
        if len(value.strip()) > 100:
            raise serializers.ValidationError(
                "La especialidad no puede exceder 100 caracteres"
            )
        return value.strip()

    def validate_club_asignado(self, value):
        """Valida que club_asignado no esté vacío y no sea solo espacios."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "El club asignado es requerido y no puede estar vacío"
            )
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El club asignado debe tener al menos 3 caracteres"
            )
        if len(value.strip()) > 100:
            raise serializers.ValidationError(
                "El club asignado no puede exceder 100 caracteres"
            )
        return value.strip()

    class Meta:
        model = Entrenador
        fields = ["especialidad", "club_asignado"]


class EntrenadorInputSerializer(serializers.Serializer):
    """Input para crear/editar entrenador + persona."""

    persona = PersonaSerializer()
    entrenador = EntrenadorDataSerializer()

    def validate(self, data):
        """Validación a nivel de objeto para asegurar que entrenador tiene datos válidos."""
        entrenador_data = data.get("entrenador", {})

        if not entrenador_data:
            raise serializers.ValidationError(
                {"entrenador": "Los datos del entrenador son requeridos"}
            )

        return data


class EntrenadorResponseSerializer(serializers.Serializer):
    """Respuesta con datos del entrenador y la persona."""

    entrenador = EntrenadorSerializer()
    persona = serializers.DictField(allow_null=True)
