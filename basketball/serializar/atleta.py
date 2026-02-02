import re
from datetime import date
from rest_framework import serializers
from ..models import Atleta, Inscripcion
from .persona import PersonaSerializer

# =============================================================================
# CONSTANTES DE VALIDACIÓN - Sincronizadas con el frontend
# =============================================================================

# Límites de caracteres para campos médicos
LIMITES_CAMPOS_MEDICOS = {
    "MAX_LENGTH": 100,
    "CAMPOS": ["alergias", "enfermedades", "medicamentos", "lesiones"],
}

# Límites de caracteres para campos de dirección
LIMITES_DIRECCION = {"MAX_LENGTH": 75}

# Mensajes de error del backend - Usados en las respuestas JSON
_MAX_MED = LIMITES_CAMPOS_MEDICOS["MAX_LENGTH"]
_MAX_DIR = LIMITES_DIRECCION["MAX_LENGTH"]
MENSAJES_ERROR_BACKEND = {
    # Campos médicos
    "ALERGIAS_MAX_LENGTH": f"El campo alergias no puede exceder {_MAX_MED} caracteres.",
    "ENFERMEDADES_MAX_LENGTH": f"El campo enfermedades no puede exceder {_MAX_MED} caracteres.",
    "MEDICAMENTOS_MAX_LENGTH": f"El campo medicamentos no puede exceder {_MAX_MED} caracteres.",
    "LESIONES_MAX_LENGTH": f"El campo lesiones no puede exceder {_MAX_MED} caracteres.",
    # Direcciones
    "DIRECCION_MAX_LENGTH": f"El campo dirección no puede exceder {_MAX_DIR} caracteres.",
    "DIRECCION_REPRESENTANTE_MAX_LENGTH": (
        f"La dirección del representante no puede exceder {_MAX_DIR} caracteres."
    ),
}


class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = "__all__"


class AtletaDataSerializer(serializers.ModelSerializer):
    """
    Datos específicos del atleta para input.

    El campo 'sexo' acepta:
    - 'Masculino' o 'Femenino' como valores estándar
    - Cualquier texto personalizado (max 20 caracteres) para opciones no binarias

    Validaciones adicionales:
    - telefono: 9-15 dígitos numéricos
    - telefono_representante: 9-15 dígitos numéricos
    - cedula_representante: 10 dígitos numéricos
    - nombre_representante: Solo letras y espacios
    """

    sexo = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Sexo del atleta. Valores: 'Masculino', 'Femenino', o texto personalizado (max 20 chars)",
    )

    def validate_sexo(self, value):
        """
        Valida el campo sexo:
        - Si es 'Masculino' o 'Femenino', se guarda tal cual
        - Si es otro valor, se permite texto libre (max 20 caracteres)
        - Se limpia whitespace
        """
        if not value:
            return value

        # Limpiar whitespace
        value = value.strip()

        if not value:
            return value

        # Validar longitud máxima
        if len(value) > 20:
            raise serializers.ValidationError(
                "El campo sexo no puede exceder 20 caracteres."
            )

        # Valores estándar (case-insensitive)
        valores_estandar = {
            "masculino": "Masculino",
            "femenino": "Femenino",
            "m": "Masculino",
            "f": "Femenino",
        }

        valor_normalizado = valores_estandar.get(value.lower())
        if valor_normalizado:
            return valor_normalizado

        # Si no es estándar, se permite texto personalizado
        # Capitalizar primera letra para consistencia
        return value.capitalize() if value else value

    def validate_telefono(self, value):
        """
        Valida el teléfono del atleta (formato Ecuador):
        - Solo dígitos numéricos
        - Exactamente 10 dígitos (formato celular: 09XXXXXXXX)

        Returns:
            str: Teléfono limpio y validado

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            return value

        # Remover caracteres de formato comunes
        value = re.sub(r"[\s\-\(\)\+]", "", value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "El teléfono debe contener solo dígitos numéricos."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "El teléfono debe tener exactamente 10 dígitos."
            )

        return value

    def validate_telefono_representante(self, value):
        """
        Valida el teléfono del representante (formato Ecuador):
        - Solo dígitos numéricos
        - Exactamente 10 dígitos

        Returns:
            str: Teléfono limpio y validado

        Raises:
            ValidationError: Si el formato es inválido
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            return value

        # Remover caracteres de formato comunes
        value = re.sub(r"[\s\-\(\)\+]", "", value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "El teléfono del representante debe contener solo dígitos numéricos."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "El teléfono del representante debe tener exactamente 10 dígitos."
            )

        return value

    def validate_cedula_representante(self, value):
        """
        Valida la cédula del representante:
        - Solo dígitos numéricos
        - Exactamente 10 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            return value

        # Remover espacios o guiones
        value = re.sub(r"[\s\-]", "", value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "La cédula del representante debe contener solo dígitos numéricos."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "La cédula del representante debe tener exactamente 10 dígitos."
            )

        return value

    def validate_nombre_representante(self, value):
        """
        Valida el nombre del representante:
        - Solo letras y espacios
        - Permite tildes y caracteres especiales del español
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            return value

        # Patrón: letras (incluyendo tildes), espacios y apóstrofes
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"

        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El nombre del representante solo puede contener letras y espacios."
            )

        # Capitalizar cada palabra
        return " ".join(word.capitalize() for word in value.split())

    # =========================================================================
    # VALIDACIONES DE CAMPOS MÉDICOS - Máximo 100 caracteres
    # =========================================================================

    def validate_alergias(self, value):
        """
        Valida el campo alergias:
        - Máximo 100 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if len(value) > LIMITES_CAMPOS_MEDICOS["MAX_LENGTH"]:
            raise serializers.ValidationError(
                MENSAJES_ERROR_BACKEND["ALERGIAS_MAX_LENGTH"]
            )

        return value

    def validate_enfermedades(self, value):
        """
        Valida el campo enfermedades:
        - Máximo 100 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if len(value) > LIMITES_CAMPOS_MEDICOS["MAX_LENGTH"]:
            raise serializers.ValidationError(
                MENSAJES_ERROR_BACKEND["ENFERMEDADES_MAX_LENGTH"]
            )

        return value

    def validate_medicamentos(self, value):
        """
        Valida el campo medicamentos:
        - Máximo 100 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if len(value) > LIMITES_CAMPOS_MEDICOS["MAX_LENGTH"]:
            raise serializers.ValidationError(
                MENSAJES_ERROR_BACKEND["MEDICAMENTOS_MAX_LENGTH"]
            )

        return value

    def validate_lesiones(self, value):
        """
        Valida el campo lesiones:
        - Máximo 100 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if len(value) > LIMITES_CAMPOS_MEDICOS["MAX_LENGTH"]:
            raise serializers.ValidationError(
                MENSAJES_ERROR_BACKEND["LESIONES_MAX_LENGTH"]
            )

        return value

    # =========================================================================
    # VALIDACIONES DE DIRECCIONES - Máximo 75 caracteres
    # =========================================================================

    def validate_direccion_representante(self, value):
        """
        Valida la dirección del representante:
        - Máximo 75 caracteres
        """
        if not value:
            return value

        value = value.strip()

        if len(value) > LIMITES_DIRECCION["MAX_LENGTH"]:
            raise serializers.ValidationError(
                MENSAJES_ERROR_BACKEND["DIRECCION_REPRESENTANTE_MAX_LENGTH"]
            )

        return value

    class Meta:
        model = Atleta
        exclude = ["persona_external", "grupos"]


class InscripcionDataSerializer(serializers.ModelSerializer):
    """
    Datos específicos de la inscripción para input.

    Validaciones:
    - fecha_inscripcion: No puede ser una fecha futura
    """

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

    class Meta:
        model = Inscripcion
        fields = ["fecha_inscripcion", "tipo_inscripcion"]


class AtletaInscripcionInputSerializer(serializers.Serializer):
    """Input para crear/editar atleta + persona + inscripcion."""

    persona = PersonaSerializer()
    atleta = AtletaDataSerializer()
    inscripcion = InscripcionDataSerializer()


class AtletaInscripcionResponseSerializer(serializers.Serializer):
    """Respuesta con datos del atleta, la persona y la inscripción."""

    atleta = serializers.DictField()
    inscripcion = serializers.DictField()
    persona = serializers.DictField(allow_null=True)
