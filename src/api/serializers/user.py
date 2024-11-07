from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The user id in the auth backend')
    name = serializers.CharField(help_text='The display name of the user')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='example user preferences',
            value={
                'display_images': User.DISPLAY_IMAGES_MODES[0],
                'display_folders': User.DISPLAY_FOLDERS_MODES[0],
            },
        ),
    ],
)
class UserPreferencesSerializer(serializers.Serializer):
    display_images = serializers.CharField()
    display_folders = serializers.CharField()

    def validate_display_images(self, value):
        if value in User.DISPLAY_IMAGES_MODES:
            return value
        display_modes = ', '.join([f"'{m}'" for m in User.DISPLAY_IMAGES_MODES])
        raise serializers.ValidationError(
            f'display_images must be one of {display_modes}',
        )

    def validate_display_folders(self, value):
        if value in User.DISPLAY_FOLDERS_MODES:
            return value
        display_modes = ', '.join([f"'{m}'" for m in User.DISPLAY_FOLDERS_MODES])
        raise serializers.ValidationError(
            f'display_folders must be one of {display_modes}',
        )


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
                    'display_images': User.DISPLAY_IMAGES_MODES[0],
                    'display_folders': User.DISPLAY_FOLDERS_MODES[0],
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
