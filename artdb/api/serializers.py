from artworks.models import Album
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from django.conf import settings
from django.utils.translation import gettext_lazy as _


class SearchFilterSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='id of the filter as obtained from the /search/filters endpoint'
    )
    filter_values = serializers.JSONField(
        help_text='Filters as defined in the /search/filters endpoint'
    )


class SearchRequestSerializer(serializers.Serializer):
    filters = serializers.ListField(
        child=SearchFilterSerializer(),
        required=False,
        help_text='Array of logical AND filters that should be applied to the search.',
    )
    exclude = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='Exclude certain artworks from the results.',
    )
    q = serializers.CharField(
        required=False, help_text='Query string for full text search.'
    )
    limit = serializers.IntegerField(
        required=False,
        default=settings.SEARCH_LIMIT,
        allow_null=False,
        help_text=f'Limit the number of results. Default: {settings.SEARCH_LIMIT}',
    )
    offset = serializers.IntegerField(
        required=False,
        default=0,
        allow_null=False,
        help_text='Offset for the first item in the results set.',
    )


class SearchArtistsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.CharField()


class SearchItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    image_original = serializers.URLField()
    credits = serializers.CharField()
    title = serializers.CharField()
    date = serializers.CharField()
    artists = SearchArtistsSerializer(many=True)

    score = serializers.FloatField()


class SearchResultSerializer(serializers.Serializer):
    label = serializers.CharField()
    total = serializers.IntegerField()
    data = SearchItemSerializer(many=True)


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The user id in the auth backend')
    name = serializers.CharField(help_text='The display name of the user')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='example user',
            value={
                'id': '0123456789ABCDEF0123456789ABCDEF',
                'name': 'Firstname Lastname',
                'email': 'addy@example.org',
                'showroom_id': 'firstname-lastname-xZy2345aceg98QPT0246aC',
                'groups': ['foo_users', 'bar_members'],
                'permissions': ['view_foo', 'view_bar', 'edit_bar'],
            },
        ),
    ],
)
class UserDataSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The user id in the auth backend')
    name = serializers.CharField(help_text='The display name of the user')
    email = serializers.CharField(help_text='The user\'s e-mail address')
    showroom_id = serializers.CharField(
        allow_null=True,
        help_text=(
            'The user\'s associated showroom id. Or null, if no associated '
            'showroom entity can be found or showroom page is deactivated'
        ),
    )
    groups = serializers.ListSerializer(
        child=serializers.CharField(), help_text='The groups this user belongs to.'
    )
    permissions = serializers.ListSerializer(
        child=serializers.CharField(), help_text='The permissions this user has.'
    )


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


class FoldersRequestSerializer(AlbumsListRequestSerializer):
    pass


class PermissionItemSerializer(serializers.Serializer):
    id = serializers.CharField()

    def validate_id(self, value):
        if value not in settings.PERMISSIONS:
            raise serializers.ValidationError(f'{value} is not a valid permission id')
        return value


class PermissionsResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    permissions = PermissionItemSerializer(many=True)


class PermissionsRequestSerializer(serializers.Serializer):
    user = serializers.CharField()
    permissions = PermissionItemSerializer(many=True)


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


class CreateAlbumRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ('title',)


class UpdateAlbumRequestSerializer(CreateAlbumRequestSerializer):
    pass


class AppendArtworkRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class SlidesRequestSerializer(serializers.Serializer):
    details = serializers.BooleanField()


class SlideSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class CreateSlidesRequestSerializer(serializers.ListSerializer):
    child = SlideSerializer(many=True)

    def validate(self, data):
        for item in data:
            if len(item) > 2:
                raise serializers.ValidationError(
                    _('No more than two artworks per slide allowed')
                )
        return data


class AlbumsRequestSerializer(serializers.Serializer):
    details = serializers.BooleanField()


class AlbumsDownloadRequestSerializer(serializers.Serializer):
    download_format = serializers.CharField(
        default='pptx', allow_null=False, allow_blank=False
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


class ArtworksImageRequestSerializer(serializers.Serializer):
    method = serializers.CharField()
    width = serializers.IntegerField(min_value=1)
    height = serializers.IntegerField(min_value=1)

    def validate_method(self, value):
        if value not in ['crop', 'resize']:
            raise serializers.ValidationError(f'{value} is not a valid method')
        return value
