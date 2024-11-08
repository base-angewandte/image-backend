from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers.user import (
    UserDataSerializer,
    UserPreferencesPatchSerializer,
    UserPreferencesSerializer,
)


class UserViewSet(viewsets.GenericViewSet):
    @extend_schema(
        tags=['user'],
        responses={
            200: UserDataSerializer,
            401: ERROR_RESPONSES[401],
        },
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a user's data and preferences."""

        attributes = request.session.get('attributes', {})
        ret = {
            'id': request.user.username,
            'name': request.user.get_full_name(),
            'email': request.user.email,
            'showroom_id': attributes.get('showroom_id'),
            'groups': attributes.get('groups'),
            'permissions': attributes.get('permissions'),
            'tos_accepted': request.user.tos_accepted,
            'preferences': request.user.preferences,
        }

        return Response(ret, status=200)

    @extend_schema(
        tags=['user'],
        request=UserPreferencesSerializer,
        responses={
            200: UserPreferencesSerializer,
            401: ERROR_RESPONSES[401],
        },
    )
    @action(detail=False, methods=['get', 'post', 'patch'])
    def preferences(self, request, *args, **kwargs):
        if request.method == 'GET':
            return Response(request.user.preferences)

        elif request.method == 'POST':
            serializer = UserPreferencesSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            request.user.display_images = serializer.validated_data['display_images']
            request.user.display_folders = serializer.validated_data['display_folders']
            request.user.save()
            return Response(request.user.preferences)

        elif request.method == 'PATCH':
            serializer = UserPreferencesPatchSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if display_images := serializer.validated_data.get('display_images'):
                request.user.display_images = display_images
            if display_folders := serializer.validated_data.get('display_folders'):
                request.user.display_folders = display_folders
            request.user.save()
            return Response(request.user.preferences)
