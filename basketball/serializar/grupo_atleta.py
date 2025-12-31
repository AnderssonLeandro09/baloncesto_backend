from rest_framework import serializers
from ..models import GrupoAtleta

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
            "first_name": persona_data.get("first_name") or persona_data.get("firts_name"),
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

class GrupoAtletaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo GrupoAtleta."""
    atletas = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False,
        help_text="Lista de IDs de atletas a asignar al grupo"
    )

    class Meta:
        model = GrupoAtleta
        fields = [
            "id", "nombre", "rango_edad_minima", "rango_edad_maxima", 
            "categoria", "entrenador", "estado", "eliminado", "atletas"
        ]

class GrupoAtletaResponseSerializer(serializers.ModelSerializer):
    """Serializer para la respuesta de GrupoAtleta con datos sanitizados de atletas."""
    atletas = serializers.SerializerMethodField()
    
    def get_atletas(self, grupo):
        """Obtiene solo los atletas con inscripción habilitada."""
        # Filtrar solo atletas con inscripción habilitada
        atletas_habilitados = []
        for atleta in grupo.atletas.all():
            try:
                if hasattr(atleta, 'inscripcion') and atleta.inscripcion.habilitada:
                    atletas_habilitados.append(atleta)
            except Exception:
                # Si no tiene inscripción o hay error, no incluir
                continue
        
        return AtletaSanitizedSerializer(atletas_habilitados, many=True).data
    
    class Meta:
        model = GrupoAtleta
        fields = [
            "id", "nombre", "rango_edad_minima", "rango_edad_maxima", 
            "categoria", "fecha_creacion", "estado", "eliminado", 
            "entrenador", "atletas"
        ]
