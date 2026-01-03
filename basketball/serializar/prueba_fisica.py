"""Serializadores para Prueba Física."""

from rest_framework import serializers
from decimal import Decimal
from datetime import date
from ..models import PruebaFisica, TipoPrueba
from .persona import PersonaMinimalSerializer


class PruebaFisicaSerializer(serializers.ModelSerializer):
    """Serializador base para Prueba Física."""

    class Meta:
        model = PruebaFisica
        fields = "__all__"


class PruebaFisicaInputSerializer(serializers.Serializer):
    """Serializador para la entrada de datos de Prueba Física."""

    atleta_id = serializers.IntegerField(required=True, min_value=1)
    fecha_registro = serializers.DateField(required=True)
    tipo_prueba = serializers.ChoiceField(choices=TipoPrueba.choices, required=True)
    resultado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal("0.01"),
        max_value=Decimal("999999.99"),
    )
    unidad_medida = serializers.CharField(
        max_length=20, required=False, allow_blank=True, allow_null=True
    )
    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=1000,  # Limitar tamaño
    )
    estado = serializers.BooleanField(default=True)

    def validate_fecha_registro(self, value):
        """Validar que la fecha no sea futura."""
        if value > date.today():
            raise serializers.ValidationError(
                "La fecha de registro no puede ser futura"
            )
        return value

    def validate_observaciones(self, value):
        """Sanitizar observaciones para prevenir XSS."""
        if value:
            # Remover caracteres potencialmente peligrosos
            import html

            return html.escape(value.strip())
        return value


class PruebaFisicaResponseSerializer(serializers.ModelSerializer):
    """Serializador para la respuesta de Prueba Física."""

    persona = PersonaMinimalSerializer(read_only=True)
    semestre = serializers.SerializerMethodField()

    class Meta:
        model = PruebaFisica
        fields = [
            "id",
            "atleta",
            "persona",
            "fecha_registro",
            "tipo_prueba",
            "resultado",
            "unidad_medida",
            "observaciones",
            "estado",
            "semestre",
        ]

    def get_semestre(self, obj):
        """Calcula el semestre automáticamente desde la fecha de registro."""
        from ..services.prueba_fisica_service import PruebaFisicaService

        return PruebaFisicaService.calcular_semestre(obj.fecha_registro)
