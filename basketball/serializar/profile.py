from rest_framework import serializers


class ProfileResponseSerializer(serializers.Serializer):
    role = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    token = serializers.CharField(required=False, allow_null=True)
    data = serializers.DictField()
