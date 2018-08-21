from rest_framework import serializers
from artworks.models import Artwork, Artist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = 'id', 'name'

class ArtworkSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    class Meta:
        model = Artwork
        fields = ('title', 'artists', 'locationOfCreation', 'date', 'material', 'dimensions', 'credits')


