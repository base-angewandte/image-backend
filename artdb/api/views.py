import json
from json import JSONDecodeError
from django.contrib.auth.models import User

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.permissions import HasAPIKey

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from artworks.models import (
    Artist,
    Keyword,
Location,
Artwork,
ArtworkCollectionMembership,


)

from artworks.serializers import (
    LocationSerializer,
    ArtistSerializer,
    KeywordSerializer,
    ArtworkSerializer,
ThumbnailSerializer,
MembershipSerializer,
CollectionSerializer,

)


class ImageAPIViewSet(viewsets.GenericViewSet):

    """
    retrieve:


    update:

    partial_update:

    """

    # serializer_class = UserPreferencesDataSerializer
    # queryset = UserPreferencesData.objects.all()
    parser_classes = (FormParser, MultiPartParser)
    filter_backends = (DjangoFilterBackend,)
    UserModel = get_user_model()

    @extend_schema(
        tags=['user'],
        request=serializer_class,
        responses={
            200: OpenApiResponse(description=''),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='User preferences object not found'),
        },
    )
    def retrieve(self, request, *args, **kwargs):
       pass

    @extend_schema(
        tags=[''],
        request=serializer_class,
        responses={
            200: OpenApiResponse(description=''),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Object not found'),
        },
    )
    def _update(self, request, partial=False, *args, **kwargs):
      pass

    @extend_schema(
        tags=[''],
        request=serializer_class,
        responses={
            200: OpenApiResponse(description=''),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Object not found'),
        },
    )
    def update(self, request, *args, **kwargs):
        pass

    @extend_schema(
        tags=[''],
        request=serializer_class,
        responses={
            200: OpenApiResponse(description=''),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Object not found'),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        pass


class UserViewSet(viewsets.GenericViewSet):
    # todo update. and user for artworks, etc
    # serializer_class = UserSerializer

    @extend_schema(
        tags=['user'],
    )
    def retrieve(self, request, *args, **kwargs):
        # attributes = get_user_preferences_attributes(request.user, '')

        data = {
        }
        return Response(data)

