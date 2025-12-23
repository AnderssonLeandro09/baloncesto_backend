from rest_framework import serializers
from ..models import GrupoAtleta

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
    """Serializer para la respuesta de GrupoAtleta, incluyendo IDs de atletas."""
    atletas = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = GrupoAtleta
        fields = [
            "id", "nombre", "rango_edad_minima", "rango_edad_maxima", 
            "categoria", "fecha_creacion", "estado", "eliminado", 
            "entrenador", "atletas"
        ]
