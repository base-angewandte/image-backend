import json

import jsonschema
from artworks.models import Album, AlbumMembership, Artist, Artwork, Keyword, Location
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from jsonschema import validate
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_json_field(value, schema):
    try:
        if not isinstance(value, list):
            value = [value]
        for v in value:
            validate(v, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(_('Well-formed but invalid JSON: {e}').format(e=e)) from e
    except json.decoder.JSONDecodeError as e:
        raise ValidationError(_('Poorly-formed text, not JSON: {e}').format(e=e)) from e
    except TypeError as e:
        raise ValidationError(_('Invalid characters: {e}').format(e=e)) from e

    # check if it is slides, because in that case duplicates are allowed.
    # The validity of slidesis checked above
    if isinstance(value, list):
        for i in value:
            if isinstance(i, list):
                if 'id' in i:  # then it is slides
                    pass
        return value

    if len(value) > len({json.dumps(d, sort_keys=True) for d in value}):
        raise ValidationError(_('Data contains duplicate entries'))

    return value


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = 'id', 'name'


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = 'id', 'name'


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = 'id', 'name'


class ArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artwork
        fields = '__all__'


class SearchFilterSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='id of the filter as obtained from the /filters endpoint'
    )
    filter_values = serializers.ListField(
        child=serializers.JSONField(),
        help_text='Array of either strings, dates, date ranges or a chips options.'
        + ' Multiple values will be combined in a logical OR.',
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
        help_text=f'Limit the number of results. Default: {settings.SEARCH_LIMIT}',
    )
    offset = serializers.IntegerField(
        required=False,
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


class ThumbnailSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    image_original = VersatileImageFieldSerializer(
        sizes=[('thumbnail', 'thumbnail__180x180')]
    )

    class Meta:
        model = Artwork
        fields = ('id', 'title', 'artists', 'image_original')


class MembershipSerializer(serializers.ModelSerializer):
    artwork = ThumbnailSerializer(read_only=True, many=False)

    class Meta:
        model = AlbumMembership
        fields = ('id', 'connected_with', 'artwork')


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


class AlbumsRequestSerializer(serializers.Serializer):
    owner = serializers.BooleanField(required=False, default=True)
    permissions = serializers.CharField(required=False, default='EDIT')

    def validate_permissions(self, value):
        for p in value.split(','):
            if p not in settings.PERMISSIONS:
                raise serializers.ValidationError(f'{p} is not a valid permission')
        return value


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
