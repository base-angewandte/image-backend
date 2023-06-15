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
    artists = ArtistSerializer(read_only=True, many=True)
    keywords = KeywordSerializer(read_only=True, many=True)
    location_of_creation = LocationSerializer(read_only=True, many=False)
    location_current = LocationSerializer(read_only=True, many=False)

    class Meta:
        model = Artwork
        fields = ('title', 'title_english', 'artists', 'location_of_creation', 'location_current', 'date', 'material',
                  'dimensions', 'keywords', 'description', 'credits', 'checked', 'published')


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


class UpdateAlbumSerializer(serializers.ModelSerializer):
    shared_info = serializers.CharField(required=False)

    class Meta:
        model = Album
        fields = '__all__'
        depth = 1


class SlidesField(serializers.JSONField):
    pass


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
