from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer

from artworks.models import Album, Artwork, Keyword, Location, Person


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = 'id', 'name'


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = 'id', 'name'


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = 'id', 'name'


class ArtworkSerializer(serializers.ModelSerializer):
    artists = PersonSerializer(read_only=True, many=True)
    keywords = KeywordSerializer(read_only=True, many=True)
    place_of_production = LocationSerializer(read_only=True, many=False)
    location = LocationSerializer(read_only=True, many=False)

    class Meta:
        model = Artwork
        fields = (
            'title',
            'title_english',
            'artists',
            'place_of_production',
            'location',
            'date',
            'material',
            'dimensions',
            'keywords',
            'comments',
            'credits',
            'checked',
            'published',
        )


class ThumbnailSerializer(serializers.ModelSerializer):
    artists = PersonSerializer(read_only=True, many=True)
    image_original = VersatileImageFieldSerializer(
        sizes=[('thumbnail', 'thumbnail__180x180')],
    )

    class Meta:
        model = Artwork
        fields = ('id', 'title', 'artists', 'image_original')


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ('title', 'members')
        depth = 1
