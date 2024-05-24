from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from api.serializers.albums import (
    AlbumResponseSerializer,
    AlbumsDownloadRequestSerializer,
    AlbumsListRequestSerializer,
    AlbumsRequestSerializer,
    AppendArtworkRequestSerializer,
    CreateAlbumRequestSerializer,
    PermissionsResponseSerializer,
    UpdateAlbumRequestSerializer,
)
from api.serializers.artworks import (
    CreateSlidesRequestSerializer,
    SlidesRequestSerializer,
)
from api.serializers.permissions import PermissionsRequestSerializer
from api.views import (
    album_object,
    check_limit,
    check_offset,
    check_sorting,
    slides_with_details,
)
from api.views.search import filter_albums_for_user
from artworks.exports import collection_download_as_pptx
from artworks.models import (
    Album,
    Artwork,
    Folder,
    FolderAlbumRelation,
    PermissionsRelation,
)


@extend_schema(tags=['albums'])
class AlbumsViewSet(viewsets.GenericViewSet):
    """
    list:
    GET all the users albums.

    create:
    POST new album with given title.

    retrieve:
    GET specific album.

    update:
    PATCH specific album and album’s fields

    destroy:
    DELETE specific album

    append_artwork
    POST /albums/{id}/append_artwork
    Append artwork to slides as singular slide [{'id': x}]

    slides:
    GET /albums/{id}/slides LIST (GET) endpoint

    create_slides:
    POST /albums/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

    permissions:
    GET /albums/{id}/permissions

    create_permissions
    POST /albums/{id}/permissions

    destroy_permissions
    DELETE /albums/{id}/permissions

    download:
    GET Download album as pptx or PDF

    """

    queryset = Album.objects.all()
    ordering_fields = ['title', 'date_created', 'date_changed']

    @extend_schema(
        parameters=[
            AlbumsListRequestSerializer,
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                required=False,
                enum=ordering_fields + [f'-{i}' for i in ordering_fields],
                default='title',
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
                    'If the response should also return shared albums, it\'s possible to define which permissions the '
                    'user needs to have for the album. Since the default is `EDIT`, shared albums with `EDIT` '
                    'permissions are included in the response.'
                ),
                default='EDIT',
            ),
        ],
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        """List of all Albums (used for getting latest Albums) /albums."""

        serializer = AlbumsListRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit = check_limit(serializer.validated_data['limit'])
        offset = check_offset(serializer.validated_data['offset'])
        sorting = check_sorting(
            request.query_params.get('sort_by', 'title'), self.ordering_fields
        )

        q_filters = filter_albums_for_user(
            user=request.user,
            owner=serializer.validated_data['owner'],
            permissions=serializer.validated_data['permissions'],
        )

        albums = Album.objects.filter(q_filters).order_by(sorting)

        total = albums.count()

        albums = albums[offset : offset + limit]

        return Response(
            {
                'total': total,
                'results': [
                    album_object(
                        album,
                        request=request,
                        details=False,
                        include_slides=False,
                        include_type=False,
                        include_featured=True,
                    )
                    for album in albums
                ],
            }
        )

    @extend_schema(
        request=CreateAlbumRequestSerializer,
        responses={
            201: AlbumResponseSerializer,
            403: ERROR_RESPONSES[403],
        },
    )
    def create(self, request, *args, **kwargs):
        """Create Album /albums/{id}"""
        serializer = CreateAlbumRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data['title']

        album = Album.objects.create(title=title, user=request.user)

        # Add album to root folder, creating a relationship
        folder = Folder.root_folder_for_user(request.user)
        FolderAlbumRelation.objects.get_or_create(
            album=album, user=request.user, folder=folder
        )

        return Response(
            album_object(album, request=request),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='details',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Boolean indicating if the response should contain details of the artworks',
                default=False,
            ),
        ],
        responses={
            200: AlbumResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        """List of Works (Slides) in a specific Album /albums/{id}"""

        serializer = AlbumsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        details = serializer.validated_data['details']

        return Response(album_object(album, request=request, details=details))

    @extend_schema(
        request=UpdateAlbumRequestSerializer,
        responses={
            200: AlbumResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def update(self, request, pk=None, *args, **kwargs):
        """Update Album /albums/{id}"""

        serializer = UpdateAlbumRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        if (
            album.user == request.user
            or PermissionsRelation.objects.filter(
                album=album,
                user=request.user,
                permissions='EDIT',
            ).exists()
        ):
            album.title = serializer.validated_data['title']
            album.save()
            return Response(album_object(album, request=request))

        raise PermissionDenied()

    @extend_schema(
        responses={
            204: OpenApiResponse(),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        """Delete Album /albums/{id}"""

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        if album.user == request.user:
            album.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise PermissionDenied()

    # additional actions

    @extend_schema(
        request=AppendArtworkRequestSerializer,
        responses={
            204: OpenApiResponse(),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['post'], url_path='append-artwork')
    def append_artwork(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/append_artwork Append artwork to slides as singular
        slide [{'id': x}]"""

        serializer = AppendArtworkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        # check if artwork exists
        try:
            Artwork.objects.get(pk=serializer.validated_data['id'])
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        if (
            album.user == request.user
            or PermissionsRelation.objects.filter(
                album=album,
                user=request.user,
                permissions='EDIT',
            ).exists()
        ):
            slide = [serializer.validated_data]
            album.slides.append(slide)
            album.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise PermissionDenied()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='details',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Boolean indicating if the response should contain details of the artworks',
                default=False,
            ),
        ],
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'])
    def slides(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/slides LIST (GET) endpoint returns:"""

        serializer = SlidesRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        if serializer.validated_data['details']:
            return Response(slides_with_details(album, request))
        else:
            return Response(album.slides)

    @extend_schema(
        request=CreateSlidesRequestSerializer,
        parameters=[
            OpenApiParameter(
                name='details',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Boolean indicating if the response should contain details of the artworks',
                default=False,
            ),
        ],
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @slides.mapping.post
    def create_slides(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/slides Reorder Slides, Separate_slides, Reorder
        artworks within slides."""

        serializer = CreateSlidesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_params_serializer = SlidesRequestSerializer(data=request.query_params)
        query_params_serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        if (
            album.user == request.user
            or PermissionsRelation.objects.filter(
                album=album,
                user=request.user,
                permissions='EDIT',
            ).exists()
        ):
            slides_list = []
            for slide in serializer.validated_data:
                current_slide = []
                for artwork in slide:
                    # check if artwork exists
                    try:
                        Artwork.objects.get(id=artwork.get('id'))
                    except Artwork.DoesNotExist as dne:
                        raise NotFound(_('Artwork does not exist')) from dne
                    current_slide.append({'id': artwork['id']})
                slides_list.append(current_slide)
            album.slides = slides_list
            album.save()

            if query_params_serializer.validated_data['details']:
                return Response(slides_with_details(album, request))
            else:
                return Response(album.slides)

        raise PermissionDenied()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                required=False,
                description='last_name or -last_name',
                default='last_name',
            )
        ],
        responses={
            200: PermissionsResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None, *args, **kwargs):
        """Get Permissions /albums/{id}/permissions."""

        sorting = check_sorting(
            request.query_params.get('sort_by', 'last_name'),
            ['last_name', '-last_name'],
        )
        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        qs = PermissionsRelation.objects.filter(album=album)

        # if the user is not the owner of the album, ony return the permissions of this user
        if album.user != request.user:
            qs = qs.filter(user=request.user)

        sorting = (
            f'user__{sorting}'
            if '-' not in sorting
            else f'-user__{sorting.replace("-", "")}'
        )

        return Response(
            [
                {
                    'user': {
                        'id': p.user.username,
                        'name': p.user.get_full_name(),
                    },
                    'permissions': [{'id': p.permissions}],
                }
                for p in qs.order_by(sorting)
            ]
        )

    @extend_schema(
        request=PermissionsRequestSerializer(many=True),
        responses={
            200: PermissionsResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @permissions.mapping.post
    def create_permissions(self, request, pk=None, *args, **kwargs):
        """Post Permissions /albums/{id}/permissions."""
        serializer = PermissionsRequestSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        try:
            album = Album.objects.filter(pk=pk, user=request.user).get()
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        users = []

        # update permissions
        for item in serializer.validated_data:
            user = item['user']

            try:
                user = User.objects.get(username=user)
            except User.DoesNotExist as dne:
                raise ParseError('User does not exist') from dne

            permissions = item['permissions']

            if permissions:
                users.append(user.username)

            for perm in permissions:
                with transaction.atomic():
                    # Only allow permission assignment if the user is not already the owner
                    if album.user == user:
                        raise ParseError('User is already the owner of album.')
                    pr, created = PermissionsRelation.objects.get_or_create(
                        album=album,
                        user=user,
                    )
                    pr.permissions = perm['id']
                    pr.save()

                    # When permission is created, add album to user's root folder
                    # Add album to root folder, creating a relationship
                    root_folder = Folder.root_folder_for_user(user)
                    FolderAlbumRelation.objects.get_or_create(
                        album=album, user=user, folder=root_folder
                    )

        # remove deleted permissions
        PermissionsRelation.objects.filter(album=album).exclude(
            user__username__in=users
        ).delete()
        # also remove albums with deleted permissions from those users' root folder
        FolderAlbumRelation.objects.filter(album=album).exclude(
            user=request.user
        ).exclude(user__username__in=users).delete()

        qs = PermissionsRelation.objects.filter(album=album)

        return Response(
            [
                {
                    'user': {
                        'id': p.user.username,
                        'name': p.user.get_full_name(),
                    },
                    'permissions': [{'id': p.permissions}],
                }
                for p in qs
            ]
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @permissions.mapping.delete
    def destroy_permissions(self, request, pk=None, *args, **kwargs):
        """Delete Permissions /albums/{id}/permissions/ "Unshare" album.

        If the user is the owner of the album, all sharing permissions
        will be deleted. If the user is just a user who this album is
        shared with, only their own sharing permission will be deleted.
        """

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        # user is owner of the album
        if album.user == request.user:
            # remove permissions for all users
            PermissionsRelation.objects.filter(album=album).delete()
            # remove album from all folders except the owner's folder
            FolderAlbumRelation.objects.filter(album=album).exclude(
                user=request.user
            ).delete()

        # album is shared with user
        else:
            PermissionsRelation.objects.filter(album=album, user=request.user).delete()
            FolderAlbumRelation.objects.filter(album=album, user=request.user).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            AlbumsDownloadRequestSerializer,
            OpenApiParameter(
                name='language',
                type=OpenApiTypes.STR,
                enum=['de', 'en'],
                default='de',
            ),
            OpenApiParameter(
                name='download_format',
                type=OpenApiTypes.STR,
                enum=['pptx', 'pdf'],
                default='pptx',
                description='At the moment, only "pptx" is available. Later on, "pdf" will also be available',
            ),
        ],
        responses={
            # TODO better response definition
            #   https://drf-spectacular.readthedocs.io/en/latest/faq.html#how-to-serve-in-memory-generated-files-or-files-in-general-outside-filefield
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
            501: OpenApiResponse(description='Not implemented yet'),
        },
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, *args, **kwargs):
        # TODO only 'pptx' is implemented at the moment, need to implement 'pdf' as well

        serializer = AlbumsDownloadRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .distinct('id')
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        download_format = serializer.validated_data['download_format']
        language = serializer.validated_data['language']

        if download_format == 'pptx':
            return collection_download_as_pptx(request, id=album.id, language=language)
        elif download_format == 'pdf':
            # TODO implement pdf creation
            return Response(
                _('Not implemented yet'),
                status.HTTP_501_NOT_IMPLEMENTED,
            )
        else:
            raise ParseError(_('Invalid format'))
