from rest_framework import serializers

from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ArtworksAlbumsRequestSerializer(serializers.Serializer):
    owner = serializers.BooleanField(
        required=False,
        default=True,
        help_text='Boolean indicating to return albums owned by this user.',
    )
    permissions = serializers.CharField(
        required=False,
        default='EDIT',
        allow_blank=True,
    )

    def validate_permissions(self, value):
        permissions = ['', *settings.PERMISSIONS]
        for p in value.split(','):
            if p not in permissions:
                raise serializers.ValidationError(f'{p} is not a valid permission')
        return value


class ArtworksImageRequestSerializer(serializers.Serializer):
    method = serializers.CharField()
    width = serializers.IntegerField(min_value=1)
    height = serializers.IntegerField(min_value=1)

    def validate_method(self, value):
        if value not in ['crop', 'resize']:
            raise serializers.ValidationError(f'{value} is not a valid method')
        return value


class SlideSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlidesRequestSerializer(serializers.Serializer):
    details = serializers.BooleanField()


class CreateSlidesRequestSerializer(serializers.ListSerializer):
    child = SlideSerializer(many=True)

    def validate(self, data):
        for item in data:
            if len(item) > 2:
                raise serializers.ValidationError(
                    _('No more than two artworks per slide allowed')
                )
        return data
