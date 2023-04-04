from artworks.models import Artwork, Artist, Keyword, Location, ArtworkCollection, ArtworkCollectionMembership
from versatileimagefield.serializers import VersatileImageFieldSerializer
from rest_framework import serializers


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
        model = ArtworkCollectionMembership
        fields = ('id', 'connected_with', 'artwork')


class UpdatedAlbumField(serializers.JSONField):
    pass


class AlbumSerializer(serializers.ModelSerializer):
    shared_info = serializers.CharField(required=False)

    class Meta:
        model = ArtworkCollection
        fields = '__all__'
        depth = 1


class SlidesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArtworkCollection  # TODO: will be Slides
        fields = '__all__'
        depth = 1

