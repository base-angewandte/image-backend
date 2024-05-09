from rest_framework import serializers

from django.conf import settings

from .user import UserSerializer


class PermissionItemSerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate_id(self, value):
        if value not in settings.PERMISSIONS:
            raise serializers.ValidationError(f'{value} is not a valid permission id')
        return value


class PermissionsRequestSerializer(serializers.Serializer):
    user = serializers.CharField()
    permissions = PermissionItemSerializer(many=True)


class PermissionsResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    permissions = PermissionItemSerializer(many=True)
