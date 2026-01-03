"""Serializadores para Prueba Antropométrica."""

from rest_framework import serializers
from ..models import PruebaAntropometrica


class PruebaAntropometricaSerializer(serializers.ModelSerializer):
    """Serializador base para Prueba Antropométrica."""

    class Meta:
        model = PruebaAntropometrica
        fields = "__all__"


class PruebaAntropometricaInputSerializer(serializers.Serializer):
    """Serializador para la entrada de datos de Prueba Antropométrica."""

    atleta_id = serializers.IntegerField(required=True)
    fecha_registro = serializers.DateField(required=True)

    peso = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
    )
    estatura = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=True,
    )
    altura_sentado = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=True,
    )
    envergadura = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=True,
    )

    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    estado = serializers.BooleanField(default=True)


class PruebaAntropometricaResponseSerializer(serializers.ModelSerializer):
    """Serializador para la respuesta de Prueba Antropométrica."""

    atleta = serializers.StringRelatedField()
    registrado_por = serializers.StringRelatedField()

    class Meta:
        model = PruebaAntropometrica
        fields = [
            "id",
            "atleta",
            "registrado_por",
            "rol_registrador",
            "fecha_registro",
            "peso",
            "estatura",
            "altura_sentado",
            "envergadura",
            "indice_masa_corporal",
            "indice_cormico",
            "observaciones",
            "estado",
        ]
