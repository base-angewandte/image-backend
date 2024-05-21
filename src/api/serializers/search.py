from rest_framework import serializers

from django.conf import settings


class SearchArtistsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.CharField()


class SearchFilterSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='id of the filter as obtained from the /search/filters endpoint'
    )
    filter_values = serializers.JSONField(
        help_text='Filters as defined in the /search/filters endpoint'
    )


class SearchItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    image_original = serializers.URLField()
    credits = serializers.CharField()
    title = serializers.CharField()
    date = serializers.CharField()
    artists = SearchArtistsSerializer(many=True)

    score = serializers.FloatField()


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


class SearchResultSerializer(serializers.Serializer):
    label = serializers.CharField()
    total = serializers.IntegerField()
    data = SearchItemSerializer(many=True)
