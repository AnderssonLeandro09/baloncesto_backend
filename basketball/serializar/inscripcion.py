from rest_framework import serializers
from ..models import Inscripcion

class InscripcionSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Inscripcion."""
    
    class Meta:
        model = Inscripcion
        fields = [
            'id', 
            'atleta', 
            'fecha_inscripcion', 
            'tipo_inscripcion', 
            'fecha_creacion', 
            'habilitada'
        ]
        read_only_fields = ['fecha_creacion']
