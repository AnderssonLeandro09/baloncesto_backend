from datetime import date
from rest_framework import serializers
from ..models import Inscripcion


class InscripcionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Inscripcion.

    Validaciones:
    - fecha_inscripcion: No puede ser una fecha futura
    """

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "atleta",
            "fecha_inscripcion",
            "tipo_inscripcion",
            "fecha_creacion",
            "habilitada",
        ]
        read_only_fields = ["fecha_creacion"]

    def validate_fecha_inscripcion(self, value):
        """
        Valida que la fecha de inscripción no sea futura.
        """
        if not value:
            return value

        if value > date.today():
            raise serializers.ValidationError(
                "La fecha de inscripción no puede ser una fecha futura."
            )

        return value
