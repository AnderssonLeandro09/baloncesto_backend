"""Serializadores para Prueba Antropométrica."""

from rest_framework import serializers
from ..models import PruebaAntropometrica, Atleta


class PruebaAntropometricaSerializer(serializers.ModelSerializer):
    """Serializador base para Prueba Antropométrica."""

    class Meta:
        model = PruebaAntropometrica
        fields = "__all__"


class PruebaAntropometricaInputSerializer(serializers.Serializer):
    """Serializador para la entrada de datos de Prueba Antropométrica."""

    # Soportar tanto 'atleta' como 'atleta_id' del frontend
    atleta = serializers.IntegerField(required=False)
    atleta_id = serializers.IntegerField(required=False)
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

    def validate(self, data):
        """Validar que al menos uno de atleta o atleta_id esté presente."""
        if not data.get("atleta") and not data.get("atleta_id"):
            raise serializers.ValidationError(
                {"atleta": "El ID del atleta es requerido"}
            )
        return data


class AtletaSimpleSerializer(serializers.ModelSerializer):
    """Serializador simple para el atleta en la respuesta."""

    nombre_atleta = serializers.SerializerMethodField()
    apellido_atleta = serializers.SerializerMethodField()

    class Meta:
        model = Atleta
        fields = [
            "id",
            "nombres",
            "apellidos",
            "cedula",
            "nombre_atleta",
            "apellido_atleta",
        ]

    def get_nombre_atleta(self, obj):
        return obj.nombres or ""

    def get_apellido_atleta(self, obj):
        return obj.apellidos or ""


class PruebaAntropometricaResponseSerializer(serializers.ModelSerializer):
    """Serializador para la respuesta de Prueba Antropométrica."""

    atleta = AtletaSimpleSerializer(read_only=True)
    registrado_por = serializers.StringRelatedField()
    imc = serializers.DecimalField(
        source="indice_masa_corporal",
        max_digits=5,
        decimal_places=2,
        read_only=True,
    )

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
            "imc",
            "indice_cormico",
            "observaciones",
            "estado",
        ]
