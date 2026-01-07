from rest_framework import serializers
from ..models import GrupoAtleta, Entrenador


class AtletaSanitizedSerializer(serializers.Serializer):
    """Serializador sanitizado para mostrar información básica del atleta en grupos."""

    id = serializers.IntegerField(read_only=True)
    persona = serializers.SerializerMethodField()
    inscripcion = serializers.SerializerMethodField()

    def get_persona(self, atleta):
        """Obtiene datos sanitizados de la persona desde el módulo externo."""
        from ..serializers import get_persona_from_user_module

        if not atleta.persona_external:
            return None

        persona_data = get_persona_from_user_module(atleta.persona_external)
        if not persona_data:
            return None

        # Retornar solo campos permitidos
        return {
            "first_name": persona_data.get("first_name")
            or persona_data.get("firts_name"),
            "last_name": persona_data.get("last_name"),
            "identification": persona_data.get("identification"),
        }

    def get_inscripcion(self, atleta):
        """Obtiene datos sanitizados de la inscripción del atleta."""
        try:
            inscripcion = atleta.inscripcion
            return {
                "id": inscripcion.id,
                "habilitada": inscripcion.habilitada,
            }
        except Exception:
            return None


class EntrenadorSanitizedSerializer(serializers.Serializer):
    """Serializador sanitizado para mostrar información básica del entrenador en grupos."""

    id = serializers.IntegerField(read_only=True)
    persona = serializers.SerializerMethodField()

    def get_persona(self, entrenador):
        """Obtiene datos sanitizados de la persona desde el módulo externo."""
        from ..serializers import get_persona_from_user_module

        if not entrenador.persona_external:
            return None

        persona_data = get_persona_from_user_module(entrenador.persona_external)
        if not persona_data:
            return None

        # Retornar solo campos permitidos
        return {
            "first_name": persona_data.get("first_name")
            or persona_data.get("firts_name"),
            "last_name": persona_data.get("last_name"),
            "identification": persona_data.get("identification"),
        }


class GrupoAtletaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo GrupoAtleta."""

    atletas = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=999999999),
        write_only=True,
        required=False,
        allow_empty=True,
        max_length=100,
        help_text="Lista de IDs de atletas a asignar al grupo (máximo 100)",
    )

    class Meta:
        model = GrupoAtleta
        fields = [
            "id",
            "nombre",
            "rango_edad_minima",
            "rango_edad_maxima",
            "categoria",
            "entrenador",
            "estado",
            "eliminado",
            "atletas",
        ]
        # Seguridad: Prevenir mass assignment de campos sensibles
        read_only_fields = ["id", "eliminado", "entrenador", "estado"]

    def validate_nombre(self, value):
        """Valida el campo nombre."""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 3 caracteres"
            )
        if len(value) > 100:
            raise serializers.ValidationError(
                "El nombre no puede exceder 100 caracteres"
            )
        # Sanitizar: quitar espacios extra
        return value.strip()

    def validate_categoria(self, value):
        """Valida el campo categoría."""
        if not value or not value.strip():
            raise serializers.ValidationError("La categoría no puede estar vacía")
        
        value_stripped = value.strip()
        
        if len(value_stripped) < 5:
            raise serializers.ValidationError(
                "La categoría debe tener al menos 5 caracteres"
            )
        if len(value_stripped) > 30:
            raise serializers.ValidationError(
                "La categoría no puede exceder 30 caracteres"
            )
        return value_stripped

    def validate_rango_edad_minima(self, value):
        """Valida la edad mínima."""
        try:
            edad = int(value)
            if edad < 10:
                raise serializers.ValidationError(
                    "La edad mínima debe ser al menos 10 años"
                )
            if edad > 50:
                raise serializers.ValidationError(
                    "La edad mínima no puede ser mayor a 50 años"
                )
            return edad
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "La edad mínima debe ser un número válido"
            )

    def validate_rango_edad_maxima(self, value):
        """Valida la edad máxima."""
        try:
            edad = int(value)
            if edad < 10:
                raise serializers.ValidationError(
                    "La edad máxima debe ser al menos 10 años"
                )
            if edad > 50:
                raise serializers.ValidationError(
                    "La edad máxima no puede ser mayor a 50 años"
                )
            return edad
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "La edad máxima debe ser un número válido"
            )

    def validate_atletas(self, value):
        """Valida la lista de IDs de atletas."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Los atletas deben ser una lista")

        if len(value) > 100:
            raise serializers.ValidationError("No se pueden asignar más de 100 atletas")

        # Validar que sean enteros positivos
        for atleta_id in value:
            try:
                aid = int(atleta_id)
                if aid <= 0:
                    raise serializers.ValidationError(
                        "Los IDs de atletas deben ser números positivos"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "Los IDs de atletas deben ser números válidos"
                )

        # Eliminar duplicados
        return list(set(value))

    def validate_estado(self, value):
        """Valida el campo estado (read-only, solo para compatibilidad)."""
        # Este campo es read_only, si llega aquí es intento de manipulación
        raise serializers.ValidationError(
            "No se puede modificar el estado directamente"
        )

    def validate_entrenador(self, value):
        """Valida el campo entrenador (read-only)."""
        # Este campo es read_only, si llega aquí es intento de manipulación
        raise serializers.ValidationError("El entrenador se asigna automáticamente")

    def validate(self, data):
        """Validaciones a nivel de objeto."""
        min_edad = data.get("rango_edad_minima")
        max_edad = data.get("rango_edad_maxima")

        # Seguridad: Asegurar que no se manipulen campos read_only
        if "estado" in data:
            raise serializers.ValidationError("No se puede modificar el estado")
        if "entrenador" in data:
            raise serializers.ValidationError("No se puede modificar el entrenador")
        if "eliminado" in data:
            raise serializers.ValidationError(
                "No se puede modificar el campo eliminado"
            )

        if min_edad is not None and max_edad is not None:
            if min_edad > max_edad:
                raise serializers.ValidationError(
                    {
                        "rango_edad_minima": "La edad mínima no puede ser mayor que la máxima"
                    }
                )

        return data


class GrupoAtletaResponseSerializer(serializers.ModelSerializer):
    """Serializer para la respuesta de GrupoAtleta con datos sanitizados de atletas y entrenador."""

    atletas = serializers.SerializerMethodField()
    entrenador = serializers.SerializerMethodField()

    def get_atletas(self, grupo):
        """Obtiene solo los atletas con inscripción habilitada."""
        # Filtrar solo atletas con inscripción habilitada
        atletas_habilitados = []
        for atleta in grupo.atletas.all():
            try:
                if hasattr(atleta, "inscripcion") and atleta.inscripcion.habilitada:
                    atletas_habilitados.append(atleta)
            except Exception:
                # Si no tiene inscripción o hay error, no incluir
                continue

        return AtletaSanitizedSerializer(atletas_habilitados, many=True).data

    def get_entrenador(self, grupo):
        """Obtiene datos sanitizados del entrenador."""
        try:
            # Obtener el entrenador por ID
            entrenador = Entrenador.objects.get(id=grupo.entrenador_id)
            return EntrenadorSanitizedSerializer(entrenador).data
        except Entrenador.DoesNotExist:
            # Si no existe el entrenador, retornar solo el ID
            return {"id": grupo.entrenador_id, "persona": None}
        except Exception:
            # En caso de cualquier otro error, retornar None
            return None

    class Meta:
        model = GrupoAtleta
        fields = [
            "id",
            "nombre",
            "rango_edad_minima",
            "rango_edad_maxima",
            "categoria",
            "fecha_creacion",
            "estado",
            "entrenador",
            "atletas",
        ]
