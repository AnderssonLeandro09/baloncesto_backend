"""Serializadores para Prueba Física."""

from rest_framework import serializers
from ..models import PruebaFisica, TipoPrueba


class PruebaFisicaSerializer(serializers.ModelSerializer):
    """Serializador base para Prueba Física."""

    class Meta:
        model = PruebaFisica
        fields = "__all__"


class PruebaFisicaInputSerializer(serializers.Serializer):
    """Serializador para la entrada de datos de Prueba Física."""

    atleta_id = serializers.IntegerField(required=True)
    fecha_registro = serializers.DateField(required=True)
    tipo_prueba = serializers.ChoiceField(choices=TipoPrueba.choices, required=True)
    resultado = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    unidad_medida = serializers.CharField(max_length=20, required=True)
    observaciones = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    estado = serializers.BooleanField(default=True)


class PruebaFisicaResponseSerializer(serializers.ModelSerializer):
    """Serializador para la respuesta de Prueba Física."""

    class Meta:
        model = PruebaFisica
        fields = [
            "id",
            "atleta",
            "fecha_registro",
            "tipo_prueba",
            "resultado",
            "unidad_medida",
            "observaciones",
            "estado",
        ]
