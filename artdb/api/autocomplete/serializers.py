from rest_framework import serializers

SOURCES = [
    'users',
    'albums',
    'titles',
    'artists',
    'keywords',
    'locations',
]


class AutocompleteRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, required=False, default=10)
    q = serializers.CharField(required=True)
    type = serializers.CharField(required=True)

    def validate_type(self, value):
        for t in value.split(','):
            if t not in SOURCES:
                raise serializers.ValidationError(f'{t} is not a valid type')
        return value


class AutocompleteResponseItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()


class AutocompleteResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    data = AutocompleteResponseItemSerializer(many=True)


class AutocompleteResponseItemIntegerIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()


class AutocompleteResponseIntegerIdSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    data = AutocompleteResponseItemIntegerIdSerializer(many=True)
