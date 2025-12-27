"""
DTOs para PruebaAntropometrica
"""

from rest_framework import serializers
from ..models import PruebaAntropometrica


class PruebaAntropometricaCreateDTO(serializers.ModelSerializer):
    """
    DTO para crear una nueva prueba antropométrica
    """

    class Meta:
        model = PruebaAntropometrica
        fields = [
            "atleta",
            "registrado_por_entrenador",
            "registrado_por_estudiante",
            "rol_registrador",
            "estatura",
            "altura_sentado",
            "envergadura",
            "peso",
            "observaciones",
        ]

    def validate(self, data):
        """
        Validaciones personalizadas
        """
        estatura = data.get("estatura")
        altura_sentado = data.get("altura_sentado")
        envergadura = data.get("envergadura")
        peso = data.get("peso")
        rol = data.get("rol_registrador")

        # Validar valores positivos
        if estatura <= 0 or peso <= 0:
            raise serializers.ValidationError("Estatura y peso deben ser positivos")

        # Validar coherencia
        if altura_sentado > estatura:
            raise serializers.ValidationError(
                "Altura sentado no puede ser mayor que estatura"
            )

        if envergadura < estatura - 5:
            raise serializers.ValidationError(
                "Envergadura debe ser al menos estatura - 5 cm"
            )

        # Validar que solo uno de los registradores esté presente
        entrenador = data.get("registrado_por_entrenador")
        estudiante = data.get("registrado_por_estudiante")

        if rol == "ENTRENADOR" and not entrenador:
            raise serializers.ValidationError(
                "Debe especificar el entrenador registrador"
            )
        if rol == "ESTUDIANTE_VINCULACION" and not estudiante:
            raise serializers.ValidationError(
                "Debe especificar el estudiante de vinculación registrador"
            )
        if entrenador and estudiante:
            raise serializers.ValidationError("Solo puede haber un registrador")

        return data


class PruebaAntropometricaResponseDTO(serializers.ModelSerializer):
    """
    DTO para respuesta de prueba antropométrica
    """

    atleta_nombre = serializers.CharField(source="atleta.nombre_atleta", read_only=True)
    atleta_apellido = serializers.CharField(
        source="atleta.apellido_atleta", read_only=True
    )
    registrado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = PruebaAntropometrica
        fields = [
            "id",
            "atleta",
            "atleta_nombre",
            "atleta_apellido",
            "registrado_por_entrenador",
            "registrado_por_estudiante",
            "rol_registrador",
            "registrado_por_nombre",
            "fecha_registro",
            "estatura",
            "altura_sentado",
            "envergadura",
            "peso",
            "indice_masa_corporal",
            "indice_cormico",
            "observaciones",
            "estado",
        ]

    def get_registrado_por_nombre(self, obj):
        if obj.rol_registrador == "ENTRENADOR" and obj.registrado_por_entrenador:
            return obj.registrado_por_entrenador.persona_external
        elif (
            obj.rol_registrador == "ESTUDIANTE_VINCULACION"
            and obj.registrado_por_estudiante
        ):
            return obj.registrado_por_estudiante.persona_external
        return None


class PruebaAntropometricaGraficaDTO(serializers.Serializer):
    """
    DTO para datos de gráfica (IMC e Índice Córmico por fecha)
    """

    fecha = serializers.DateTimeField()
    imc = serializers.DecimalField(max_digits=5, decimal_places=2)
    indice_cormico = serializers.DecimalField(max_digits=5, decimal_places=2)
