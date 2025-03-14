from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from artworks.models import Folder

from ..serializers.folders import FoldersRequestSerializer
from ..views import album_object, check_limit, check_offset, check_sorting
from . import filter_albums_for_user


@extend_schema(tags=['folders'])
class FoldersViewSet(viewsets.GenericViewSet):
    queryset = Folder.objects.all()
    ordering_fields = ['title', 'date_created', 'date_changed']

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                required=False,
                enum=ordering_fields + [f'-{i}' for i in ordering_fields],
                default='title',
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                description='',
                default=100,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                required=False,
                description='',
            ),
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        """List of all Folders for a user.

        At the moment users only have one root Folder.
        """

        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))
        sorting = check_sorting(
            request.query_params.get('sort_by', 'title'),
            self.ordering_fields,
        )

        results = (
            self.queryset.filter(owner=request.user)
            .order_by(sorting)
            .select_related('owner')
        )
        results = results[offset : offset + limit]

        return Response(
            [
                {
                    'id': folder.id,
                    'title': folder.title,
                    'owner': folder.owner.get_full_name(),
                }
                for folder in results
            ],
        )

    @extend_schema(
        parameters=[
            FoldersRequestSerializer,
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                required=False,
                enum=ordering_fields + [f'-{i}' for i in ordering_fields],
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                description='',
                default=100,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='permissions',
                type={
                    'type': 'array',
                    'items': {'type': 'string', 'enum': settings.PERMISSIONS},
                },
                location=OpenApiParameter.QUERY,
                required=False,
                style='form',
                explode=False,
                description=(
                    "If the response should also return shared albums, it's possible to define which permissions the "
                    'user needs to have for the album. Since the default is `EDIT`, shared albums with `EDIT` '
                    'permissions are included in the response.'
                ),
                default='EDIT',
            ),
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, *args, pk=None, **kwargs):
        """Retrieve information for a specific Folder.

        If id == 'root' it returns the content of the root folder for
        the current user.
        """

        serializer = FoldersRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))
        sorting = check_sorting(
            request.query_params.get('sort_by', 'title'),
            self.ordering_fields,
        )

        # Retrieve folder by id
        if pk == 'root':
            folder = Folder.root_folder_for_user(request.user)
        else:
            # As we now only have root folder, this is not immediately useful
            # But I am leaving it here in case someone was searching something other than root
            try:
                folder = Folder.objects.get(owner=request.user, id=pk)
            except Folder.DoesNotExist as dne:
                raise NotFound(_('Folder does not exist')) from dne

        q_filters = filter_albums_for_user(
            user=request.user,
            owner=serializer.validated_data['owner'],
            permissions=serializer.validated_data['permissions'],
        )

        albums = (
            folder.albums.filter(q_filters)
            .order_by(sorting)
            .select_related(
                'user',
                'last_changed_by',
            )[offset : offset + limit]
        )

        albums_data = [
            album_object(
                album,
                request=request,
                details=False,
                include_slides=False,
                include_type=True,
                include_featured=True,
            )
            for album in albums
        ]
        return Response(
            {
                'id': folder.id,
                'title': folder.title,
                'content': {
                    # Content shows all the albums belonging to the (root) folder per user.
                    # As at the moment we only have root folders, folders within folders
                    # will later be implemented to be shown in content
                    'total': folder.albums.all().count(),  # currently: number of albums belonging to root folder
                    'data': albums_data,
                },
            },
        )
