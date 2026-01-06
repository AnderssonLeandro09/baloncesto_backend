"""Serializadores para Prueba Antropométrica."""

from decimal import Decimal
from datetime import date, timedelta
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

    def to_internal_value(self, data):
        """Convertir enteros a decimales antes de validar."""
        campos_decimales = ['peso', 'estatura', 'altura_sentado', 'envergadura']
        
        for campo in campos_decimales:
            if campo in data and isinstance(data[campo], (int, str)):
                try:
                    # Asegurar que sea Decimal con 2 decimales
                    data[campo] = Decimal(str(data[campo])).quantize(Decimal('0.01'))
                except:
                    pass  # Dejar que la validación normal maneje el error
        
        return super().to_internal_value(data)

    def validate_peso(self, value):
        """Validar peso razonable para baloncesto (kg)."""
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor a 0 kg")
        if value < Decimal("20.0"):
            raise serializers.ValidationError("El peso es muy bajo (mínimo 20 kg)")
        if value > Decimal("200.0"):
            raise serializers.ValidationError("El peso es muy alto (máximo 200 kg)")
        return value
    
    def validate_estatura(self, value):
        """Validar estatura razonable (metros)."""
        if value <= 0:
            raise serializers.ValidationError("La estatura debe ser mayor a 0 m")
        if value < Decimal("1.0"):
            raise serializers.ValidationError("La estatura es muy baja (mínimo 1.0 m)")
        if value > Decimal("2.5"):
            raise serializers.ValidationError("La estatura es muy alta (máximo 2.5 m)")
        return value
    
    def validate_altura_sentado(self, value):
        """Validar altura sentado razonable (metros)."""
        if value <= 0:
            raise serializers.ValidationError("La altura sentado debe ser mayor a 0 m")
        if value < Decimal("0.5"):
            raise serializers.ValidationError("La altura sentado es muy baja (mínimo 0.5 m)")
        if value > Decimal("1.5"):
            raise serializers.ValidationError("La altura sentado es muy alta (máximo 1.5 m)")
        return value
    
    def validate_envergadura(self, value):
        """Validar envergadura razonable (metros)."""
        if value <= 0:
            raise serializers.ValidationError("La envergadura debe ser mayor a 0 m")
        if value < Decimal("1.0"):
            raise serializers.ValidationError("La envergadura es muy baja (mínimo 1.0 m)")
        if value > Decimal("3.0"):
            raise serializers.ValidationError("La envergadura es muy alta (máximo 3.0 m)")
        return value
    
    def validate_fecha_registro(self, value):
        """Validar que la fecha sea razonable."""
        hoy = date.today()
        
        # No permitir fechas futuras
        if value > hoy:
            raise serializers.ValidationError("La fecha no puede ser futura")
        
        # No permitir fechas muy antiguas (ejemplo: más de 10 años)
        fecha_minima = hoy - timedelta(days=365 * 10)
        if value < fecha_minima:
            raise serializers.ValidationError(
                f"La fecha no puede ser anterior a {fecha_minima.strftime('%d/%m/%Y')}"
            )
        
        return value

    def validate(self, data):
        """Validaciones cruzadas entre campos."""
        # Validación existente
        if not data.get("atleta") and not data.get("atleta_id"):
            raise serializers.ValidationError(
                {"atleta": "El ID del atleta es requerido"}
            )
        
        # Validar que altura_sentado no sea mayor que estatura
        estatura = data.get("estatura")
        altura_sentado = data.get("altura_sentado")
        
        if estatura and altura_sentado:
            if altura_sentado > estatura:
                raise serializers.ValidationError({
                    "altura_sentado": "La altura sentado no puede ser mayor que la estatura"
                })
            
            # Validar que altura_sentado sea al menos 40% de la estatura
            if altura_sentado < (estatura * Decimal("0.4")):
                raise serializers.ValidationError({
                    "altura_sentado": "La altura sentado parece incorrecta (muy baja respecto a estatura)"
                })
        
        # Validar relación envergadura-estatura (usualmente entre 0.9 y 1.4)
        envergadura = data.get("envergadura")
        if estatura and envergadura:
            ratio = envergadura / estatura
            if ratio < Decimal("0.9") or ratio > Decimal("1.4"):
                raise serializers.ValidationError({
                    "envergadura": f"La relación envergadura/estatura ({ratio:.2f}) es inusual. Verifica los datos."
                })
        
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

    atleta = serializers.SerializerMethodField()
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

    def get_atleta(self, obj):
        """Permite serializar mocks (string) sin romper la lógica real."""
        atleta = getattr(obj, "atleta", None)

        if isinstance(atleta, Atleta):
            return AtletaSimpleSerializer(atleta).data

        if isinstance(atleta, str):
            return {
                "id": None,
                "nombres": atleta,
                "apellidos": "",
                "cedula": "",
                "nombre_atleta": atleta,
                "apellido_atleta": "",
            }

        return None
