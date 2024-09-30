from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The user id in the auth backend')
    name = serializers.CharField(help_text='The display name of the user')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='example user preferences',
            value={
                'display_images': 'crop',
                'display_folders': 'list',
            },
        ),
    ],
)
class UserPreferencesSerializer(serializers.Serializer):
    display_images = serializers.CharField()
    display_folders = serializers.CharField()

    def validate_display_images(self, value):
        valid = ['crop', 'resize']
        if value in valid:
            return value
        raise serializers.ValidationError(f'display_images must be one of {valid}')

    def validate_display_folders(self, value):
        valid = ['list', 'grid']
        if value in valid:
            return value
        raise serializers.ValidationError(f'display_folders must be one of {valid}')


class UserPreferencesPatchSerializer(UserPreferencesSerializer):
    display_images = serializers.CharField(required=False)
    display_folders = serializers.CharField(required=False)


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
                'tos_accepted': False,
                'preferences': {
                    'display_images': 'crop',
                    'display_folders': 'list',
                },
            },
        ),
    ],
)
class UserDataSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The user id in the auth backend')
    name = serializers.CharField(help_text='The display name of the user')
    email = serializers.CharField(help_text="The user's e-mail address")
    showroom_id = serializers.CharField(
        allow_null=True,
        help_text=(
            "The user's associated showroom id. Or null, if no associated "
            'showroom entity can be found or showroom page is deactivated'
        ),
    )
    groups = serializers.ListSerializer(
        child=serializers.CharField(),
        help_text='The groups this user belongs to.',
    )
    permissions = serializers.ListSerializer(
        child=serializers.CharField(),
        help_text='The permissions this user has.',
    )
    tos_accepted = serializers.BooleanField(help_text="The user's tos accepted status")
    preferences = UserPreferencesSerializer()
