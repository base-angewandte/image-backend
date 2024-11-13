from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from artworks.models import Album

from .artworks import ArtworksAlbumsRequestSerializer
from .permissions import PermissionsResponseSerializer
from .user import UserSerializer


class CreateAlbumRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ('title',)


class UpdateAlbumRequestSerializer(CreateAlbumRequestSerializer):
    pass


class AppendArtworkRequestSerializer(serializers.Serializer):
    id = serializers.CharField()


class AlbumsListRequestSerializer(ArtworksAlbumsRequestSerializer):
    limit = serializers.IntegerField(
        required=False,
        default=10,
        allow_null=False,
        help_text='Limit the number of results.',
    )
    offset = serializers.IntegerField(
        required=False,
        default=0,
        allow_null=False,
        help_text='Offset for the first item in the results set.',
    )


class AlbumsRequestSerializer(serializers.Serializer):
    details = serializers.BooleanField()


class AlbumsDownloadRequestSerializer(serializers.Serializer):
    download_format = serializers.CharField(
        default='pptx',
        allow_null=False,
        allow_blank=False,
    )
    language = serializers.CharField(default='de', allow_null=False, allow_blank=False)

    def validate_download_format(self, value):
        if value not in ['pptx', 'pdf']:
            raise serializers.ValidationError(f'{value} is not a valid format')
        return value

    def validate_language(self, value):
        if value not in ['de', 'en']:
            raise serializers.ValidationError(f'{value} is not a valid language')
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='example album',
            value={
                'id': 2,
                'title': 'Example Album',
                'number_of_artworks': 3,
                'slides': [[{'id': 123}], [{'id': 234}, {'id': 345}]],
                'owner': {
                    'id': '0123456789ABCDEF0123456789ABCDEF',
                    'name': 'Firstname Lastname',
                },
                'permissions': [
                    {
                        'user': {
                            'id': '123456789ABCDEF0123456789ABCDEFG',
                            'name': 'Robin Smith',
                        },
                        'permissions': [{'id': 'VIEW'}],
                    },
                ],
            },
        ),
    ],
)
class AlbumResponseSerializer(serializers.ModelSerializer):
    number_of_artworks = serializers.IntegerField()
    owner = UserSerializer()
    permissions = PermissionsResponseSerializer(many=True)

    class Meta:
        model = Album
        fields = [
            'id',
            'title',
            'number_of_artworks',
            'slides',
            'owner',
            'permissions',
        ]
