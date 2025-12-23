from rest_framework import serializers
from ..models import Entrenador

class EntrenadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrenador
        fields = "__all__"
