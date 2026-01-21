from rest_framework import serializers
from ..models import EstudianteVinculacion
from .persona import PersonaSerializer


class EstudianteVinculacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstudianteVinculacion
        fields = "__all__"


class EstudianteVinculacionDataSerializer(serializers.ModelSerializer):
    """Datos específicos del estudiante de vinculación."""

    def validate_semestre(self, value):
        """Valida que el semestre esté en un rango permitido (1-10 o A-J)."""
        if not value:
            return value

        value = value.strip().upper()
        # Permitir números del 1 al 10 o letras de la A a la J
        valid_options = [str(i) for i in range(1, 11)] + [
            chr(i) for i in range(ord("A"), ord("K"))
        ]

        if value not in valid_options:
            raise serializers.ValidationError(
                "Semestre inválido. Use números (1-10) o letras (A-J)."
            )
        return value

    def validate_carrera(self, value):
        """Valida longitud mínima y contenido de la carrera."""
        if not value:
            return value

        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError(
                "El nombre de la carrera debe tener al menos 5 caracteres."
            )
        return value

    class Meta:
        model = EstudianteVinculacion
        fields = ["carrera", "semestre"]


class EstudianteVinculacionInputSerializer(serializers.Serializer):
    """Input para crear/editar estudiante de vinculación + persona."""

    persona = PersonaSerializer()
    estudiante = EstudianteVinculacionDataSerializer()


class EstudianteVinculacionResponseSerializer(serializers.Serializer):
    """Respuesta con datos del estudiante y la persona."""

    estudiante = EstudianteVinculacionSerializer()
    persona = serializers.DictField(allow_null=True)
