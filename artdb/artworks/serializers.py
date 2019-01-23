from rest_framework import serializers
from artworks.models import Artwork, Artist, Keyword, Location, ArtworkCollection, ArtworkCollectionMembership
from versatileimagefield.serializers import VersatileImageFieldSerializer

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


# TODO: delete? needed?
class ArtworkSerializerGerman(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    keywords = KeywordSerializer(read_only=True, many=True)
    locationOfCreation = LocationSerializer(read_only=True, many=False)

    class Meta:
        model = Artwork
        fields = ('title', 'titleEnglish', 'artists', 'locationOfCreation', 'date', 'material', 'dimensions', 'keywords', 'credits')



class ThumbnailSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(read_only=True, many=True)
    imageOriginal = VersatileImageFieldSerializer(sizes=[
            ('thumbnail', 'thumbnail__180x180')])
    
    class Meta:
        model = Artwork
        fields = ('id', 'title', 'artists', 'imageOriginal')


class MembershipSerializer(serializers.ModelSerializer):
    artwork = ThumbnailSerializer(read_only=True, many=False)

    class Meta:
        model = ArtworkCollectionMembership
        fields = ('id', 'connectedWith', 'artwork')


class CollectionSerializer(serializers.ModelSerializer):
    members = MembershipSerializer(source='artworkcollectionmembership_set',read_only=True, many=True)

    class Meta:
        model = ArtworkCollection
        fields = ('title', 'members')
        depth = 1