import re
from rest_framework import serializers


class PersonaSerializer(serializers.Serializer):
    """
    Datos de la persona en el microservicio de usuarios.
    MODO FAIL-SAFE: Todos los campos excepto identification son opcionales.

    Validaciones:
    - first_name/last_name: Solo letras y espacios
    - identification: 10 dígitos numéricos (cédula ecuatoriana)
    - phono: 9-15 dígitos numéricos
    """

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación (10 dígitos)"
    )

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    # Usamos CharField y required=False para que no valide formato ni existencia obligatoria
    email = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    password = serializers.CharField(
        required=False, write_only=True, allow_null=True, allow_blank=True
    )

    phono = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Teléfono/Celular (9-15 dígitos)",
    )

    gender = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    direction = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    type_identification = serializers.CharField(required=False, default="CEDULA")
    type_stament = serializers.CharField(required=False, default="ESTUDIANTES")

    # =========================================================================
    # VALIDACIONES PERSONALIZADAS
    # =========================================================================

    def validate_first_name(self, value):
        """
        Valida que el nombre solo contenga letras y espacios.
        Permite caracteres con tildes (á, é, í, ó, ú, ñ).
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            raise serializers.ValidationError("El nombre es requerido.")

        # Patrón: letras (incluyendo tildes), espacios y apóstrofes
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"

        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )

        # Capitalizar cada palabra
        return " ".join(word.capitalize() for word in value.split())

    def validate_last_name(self, value):
        """
        Valida que el apellido solo contenga letras y espacios.
        Permite caracteres con tildes (á, é, í, ó, ú, ñ).
        """
        if not value:
            return value

        value = value.strip()

        if not value:
            raise serializers.ValidationError("El apellido es requerido.")

        # Patrón: letras (incluyendo tildes), espacios y apóstrofes
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s']+$"

        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El apellido solo puede contener letras y espacios."
            )

        # Capitalizar cada palabra
        return " ".join(word.capitalize() for word in value.split())

    def validate_identification(self, value):
        """
        Valida la cédula ecuatoriana:
        - Debe contener exactamente 10 dígitos numéricos
        - No puede estar vacía
        - Debe cumplir con el algoritmo del dígito verificador (Módulo 10)
        """
        if not value:
            raise serializers.ValidationError("La cédula es requerida.")

        value = value.strip()

        # Remover espacios o guiones que el usuario pueda haber ingresado
        value = re.sub(r"[\s\-]", "", value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "La cédula debe contener solo dígitos numéricos."
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "La cédula debe tener exactamente 10 dígitos."
            )

        # Algoritmo de validación de cédula ecuatoriana (Módulo 10)
        provincia = int(value[0:2])
        if provincia < 1 or provincia > 24:
            raise serializers.ValidationError("Código de provincia inválido.")

        tercer_digito = int(value[2])
        if tercer_digito >= 6:
            raise serializers.ValidationError("Cédula inválida.")

        # Pesos correspondientes a cada posición
        coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        suma = 0
        for i in range(9):
            valor = int(value[i]) * coeficientes[i]
            if valor >= 10:
                valor -= 9
            suma += valor

        total = (suma % 10) if (suma % 10) == 0 else (10 - (suma % 10))
        verificador = int(value[9])

        if total != verificador:
            raise serializers.ValidationError("La cédula no es válida.")

        return value

    def validate_password(self, value):
        """
        Valida la complejidad de la contraseña:
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos un número
        """
        if not value:
            return value

        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )
        return value

    def validate_gender(self, value):
        """Valida que el género sea uno de los permitidos."""
        if not value:
            return value

        value = value.strip().capitalize()
        permitidos = ["Masculino", "Femenino", "Otro"]
        if value not in permitidos:
            raise serializers.ValidationError(
                f"Género inválido. Debe ser uno de: {', '.join(permitidos)}"
            )
        return value

    def validate_phono(self, value):
        """
        Valida el número de teléfono (formato Ecuador):
        - Solo dígitos numéricos
        - Exactamente 10 dígitos (celular: 09XXXXXXXX)

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

        # Remover espacios, guiones y paréntesis comunes en teléfonos
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

class PersonaEstudianteSerializer(PersonaSerializer):
    """
    Serializer para Estudiante de Vinculación.
    Permite identificaciones de cualquier longitud (para otros países).
    Deshabilita la validación específica de cédula ecuatoriana.
    """

    def validate_identification(self, value):
        if not value:
            raise serializers.ValidationError("La identificación es requerida.")

        value = value.strip()
        # Remover espacios o guiones
        value = re.sub(r"[\s\-]", "", value)

        if not value.isdigit():
            raise serializers.ValidationError(
                "La identificación debe contener solo dígitos numéricos."
            )

        # Se elimina la validación de 10 dígitos y algoritmo de Ecuador
        return value

class PersonaMinimalSerializer(serializers.Serializer):
    """
    Serializer mínimo para datos de persona.
    Solo contiene los campos esenciales.
    """

    identification = serializers.CharField(
        required=True, help_text="Cédula o identificación"
    )
    first_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
