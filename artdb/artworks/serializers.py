from rest_framework import serializers
from artworks.models import Artwork, Artist, Keyword, Location


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
    locationOfCreation = LocationSerializer(read_only=True, many=False)

    class Meta:
        model = Artwork
        fields = ('title', 'titleEnglish', 'artists', 'locationOfCreation', 'date', 'material', 'dimensions', 'keywords', 'credits')


class ArtworkSerializerGerman(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    keywords = KeywordSerializer(read_only=True, many=True)
    locationOfCreation = LocationSerializer(read_only=True, many=False)

    class Meta:
        model = Artwork
        fields = ('title', 'titleEnglish', 'artists', 'locationOfCreation', 'date', 'material', 'dimensions', 'keywords', 'credits')