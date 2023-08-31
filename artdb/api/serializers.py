from artworks.models import Artwork, Artist, Keyword, Location, Album, AlbumMembership
from versatileimagefield.serializers import VersatileImageFieldSerializer
from rest_framework import serializers
from django.core.exceptions import ValidationError
import jsonschema
from jsonschema import validate
import json
from django.utils.translation import gettext_lazy as _


def validate_json_field(value, schema):
    try:
        if not isinstance(value, list):
            value = [value]
        for v in value:
            validate(v, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(_(f'Well-formed but invalid JSON: {e}')) from e
    except json.decoder.JSONDecodeError as e:
        raise ValidationError(_(f'Poorly-formed text, not JSON: {e}')) from e
    except TypeError as e:
        raise ValidationError(f'Invalid characters: {e}') from e

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


class SearchRequestField(serializers.JSONField):
    pass


class SearchRequestSerializer(serializers.ModelSerializer):
    search_request = SearchRequestField(
        label=_('Search'),
        required=False,
        allow_null=True,
        default=[
            {
                'limit': 0,
                'offset': 0,
                'exclude': ['id123', 'id345'],  # with artwork ids
                'q': 'searchstring',  # the string from general search
                'filters':
                    [
                        {
                            'id': 'artist',
                            'filter_values': ['rubens', {'id': 'id786'}],
                        }
                    ],
            }
        ],
    )

    def validate_search_request(self, value):
        schema = {
            'type': 'object',
            'properties': {
                'limit': {'type': 'integer'},
                'offset': {'type': 'integer'},
                'exclude': {
                    'type': 'array',
                    'items': {'type': 'string'}
                },
                'q': {'type': 'string'},
                'filters': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'filter_values': {
                                    'oneOf': [
                                        {
                                            'type': 'array',
                                            'items': {
                                                'anyOf': [
                                                    {'type': 'string'},
                                                    {'type': 'object',
                                                     'properties': {
                                                         'id': {'type': 'string'},
                                                     },
                                                     }
                                                ]
                                            }
                                        },
                                        {
                                            'type': 'object',
                                            'properties': {
                                                'date_from': {'type': 'string'},
                                                'date_to': {'type': 'string'}
                                            }
                                        }
                                    ]
                            }



                        }
                    }
                },
            },
        }
        return validate_json_field(value, schema)

    class Meta:
        model = Album
        fields = ('search_request',)
        depth = 1


class SearchResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artwork
        fields = '__all__'


class ThumbnailSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    image_original = VersatileImageFieldSerializer(sizes=[
        ('thumbnail', 'thumbnail__180x180')])

    class Meta:
        model = Artwork
        fields = ('id', 'title', 'artists', 'image_original')


class MembershipSerializer(serializers.ModelSerializer):
    artwork = ThumbnailSerializer(read_only=True, many=False)

    class Meta:
        model = AlbumMembership
        fields = ('id', 'connected_with', 'artwork')


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'
        depth = 1


class CreateAlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ('title',)
        depth = 1


class SlidesField(serializers.JSONField):
    pass

class PermissionsField(serializers.JSONField):
    pass


class UpdateAlbumSerializer(serializers.ModelSerializer):

    class Meta:
        model = Album
        fields = ('title',)
        depth = 1


class PermissionsSerializer(UpdateAlbumSerializer):
    permissions = PermissionsField(
        label=_('Permissions'),
        required=False,
        allow_null=True,
        default=[
            {
                "user_id": "123xd3",
                "permissions": {
                    "id": "read"
                }
            }
        ],
    )

    def validate_permissions(self, value):
        schema = {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string'},
                    'permissions': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'}
                        }
                    }
                },
        }
        return validate_json_field(value, schema)

    class Meta:
        model = Album
        fields = ('permissions',)
        depth = 1


class SlidesSerializer(serializers.ModelSerializer):
    slides = SlidesField(
        label=_('Slides'),
        required=False,
        allow_null=True,
        default=[[]],
    )

    def validate_slides(self, value):
        schema = {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                },
            }
        }
        return validate_json_field(value, schema)

    class Meta:
        model = Album
        fields = ('slides',)
        depth = 1
