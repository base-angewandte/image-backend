import logging
import zipfile
from io import BytesIO

from artworks.exports import collection_download_as_pptx
from artworks.models import (
    Album,
    Artwork,
    DiscriminatoryTerm,
    Folder,
    FolderAlbumRelation,
    Keyword,
    Location,
    PermissionsRelation,
)
from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.serializers import JSONField

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, FloatField, Q, Value, Window
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .search.filters import FILTERS, FILTERS_KEYS
from .serializers import (
    AlbumResponseSerializer,
    AlbumsDownloadRequestSerializer,
    AlbumsListRequestSerializer,
    AlbumsRequestSerializer,
    AppendArtworkRequestSerializer,
    ArtworksAlbumsRequestSerializer,
    ArtworksImageRequestSerializer,
    CreateAlbumRequestSerializer,
    CreateSlidesRequestSerializer,
    FolderSerializer,
    FoldersRequestSerializer,
    PermissionsRequestSerializer,
    PermissionsResponseSerializer,
    SearchRequestSerializer,
    SearchResultSerializer,
    SlidesRequestSerializer,
    UpdateAlbumRequestSerializer,
    UserDataSerializer,
)

logger = logging.getLogger(__name__)


def check_limit(limit):
    try:
        limit = int(limit)
        if limit <= 0:
            raise ValueError
    except ValueError as e:
        raise ParseError(_('limit must be a positive integer')) from e

    return limit


def check_offset(offset):
    try:
        offset = int(offset)
        if offset < 0:
            raise ParseError(_('negative offset is not allowed'))
    except ValueError as e:
        raise ParseError(_('offset must be an integer')) from e

    return offset


def check_sorting(sorting, ordering_fields):
    try:
        sorting = str(sorting)
        if sorting not in ordering_fields + [f'-{i}' for i in ordering_fields]:
            raise ParseError(_(f'sorting should be {ordering_fields}'))
    except ValueError as e:
        raise ParseError(_('sorting must be a string')) from e

    return sorting


def slides_with_details(album, request):
    ret = []
    for slide in album.slides:
        slide_info = []
        for artwork in slide:
            try:
                artwork = Artwork.objects.get(id=artwork.get('id'))
            except Artwork.DoesNotExist as dne:
                raise NotFound(_('Artwork does not exist')) from dne

            slide_info.append(
                {
                    'id': artwork.id,
                    'image_original': request.build_absolute_uri(
                        artwork.image_original.url
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                    'credits': artwork.credits,
                    'date': artwork.date,
                    'artists': [
                        {
                            'id': artist.id,
                            'value': artist.name,
                        }
                        for artist in artwork.artists.all()
                    ],
                }
            )
        ret.append(slide_info)

    return ret


def album_object(album, request=None, details=False):
    permissions_qs = PermissionsRelation.objects.filter(album=album)

    if request is not None and album.user != request.user:
        permissions_qs = permissions_qs.filter(user=request.user)

    return {
        'id': album.id,
        'title': album.title,
        'number_of_artworks': album.size(),
        'slides': slides_with_details(album, request) if details else album.slides,
        'owner': {
            'id': album.user.username,
            'name': album.user.get_full_name(),
        },
        'permissions': [
            {
                'user': {
                    'id': p.user.username,
                    'name': p.user.get_full_name(),
                },
                'permissions': [{'id': p.permissions}],
            }
            for p in permissions_qs
        ],
    }


@extend_schema(tags=['artworks'])
class ArtworksViewSet(viewsets.GenericViewSet):
    """
    list:
    GET all artworks.

    retrieve:
    GET specific artwork.

    retrieve_albums:
    GET albums the current user has added this artwork to.

    download:
    GET Download artwork + metadata

    """

    queryset = Artwork.objects.filter(published=True)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                default=100,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                required=False,
                default=0,
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
        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))

        results = self.get_queryset()

        total = results.count()

        results = results[offset : offset + limit]

        return Response(
            {
                'total': total,
                'results': [
                    {
                        'id': artwork.id,
                        'image_original': request.build_absolute_uri(
                            artwork.image_original.url
                        )
                        if artwork.image_original
                        else None,
                        'credits': artwork.credits,
                        'title': artwork.title,
                        'date': artwork.date,
                        'artists': [
                            {'id': artist.id, 'value': artist.name}
                            for artist in artwork.artists.all()
                        ],
                    }
                    for artwork in results
                ],
            }
        )

    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne
        except ValueError as ve:
            raise ParseError(_('Artwork id must be of type integer')) from ve

        return Response(
            {
                'id': artwork.id,
                'image_original': request.build_absolute_uri(artwork.image_original.url)
                if artwork.image_original
                else None,
                'credits': artwork.credits,
                'license': '',  # placeholder for future field change, see ticket 2070
                'title': artwork.title,
                'title_english': artwork.title_english,
                'title_notes': '',  # placeholder for future field change, see ticket 2070
                'date': artwork.date,
                'material': artwork.material,
                'dimensions': artwork.dimensions,
                'description': artwork.description,
                'place_of_production': {
                    'id': artwork.place_of_production.id,
                    'value': artwork.place_of_production.name,
                }
                if artwork.place_of_production
                else {},
                'location': {
                    'id': artwork.location.id,
                    'value': artwork.location.name,
                }
                if artwork.location
                else {},
                'artists': [
                    {'id': artist.id, 'value': artist.name}
                    for artist in artwork.artists.all()
                ],
                'keywords': [
                    {'id': keyword.id, 'value': keyword.name}
                    for keyword in artwork.keywords.all()
                ],
            }
        )

    # additional actions

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='method',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                enum=(
                    'crop',
                    'resize',
                ),
            ),
            OpenApiParameter(
                name='width',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name='height',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
        responses={
            # TODO better response definition
            302: OpenApiResponse(),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='image/(?P<method>[a-z]+)/(?P<width>[0-9]+)x(?P<height>[0-9]+)',
    )
    def image(self, request, pk=None, *args, **kwargs):
        serializer = ArtworksImageRequestSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne
        method = serializer.validated_data['method']
        size = f'{serializer.validated_data["width"]}x{serializer.validated_data["height"]}'
        match method:
            case 'resize':
                url = artwork.image_original.thumbnail[size].url
            case 'crop':
                url = artwork.image_original.crop[size].url
            case _:
                url = artwork.image_original.url
        return redirect(request.build_absolute_uri(url))

    @extend_schema(
        parameters=[
            ArtworksAlbumsRequestSerializer,
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
    @action(detail=True, methods=['get'], url_path='albums')
    def retrieve_albums(self, request, pk=None, *args, **kwargs):
        serializer = ArtworksAlbumsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        q_filters = Q()

        if serializer.validated_data['owner']:
            q_filters |= Q(user=request.user)

        permissions = serializer.validated_data['permissions'].split(',')

        if permissions:
            q_filters |= Q(
                pk__in=PermissionsRelation.objects.filter(
                    user=request.user,
                    permissions__in=permissions,
                ).values_list('album__pk', flat=True)
            )

        albums = Album.objects.filter(slides__contains=[[{'id': artwork.pk}]]).filter(
            q_filters
        )

        return Response(
            [
                {
                    'id': album.id,
                    'title': album.title,
                }
                for album in albums
            ]
        )

    @extend_schema(
        responses={
            # TODO better response definition
            #   https://drf-spectacular.readthedocs.io/en/latest/faq.html#how-to-serve-in-memory-generated-files-or-files-in-general-outside-filefield
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
            500: OpenApiResponse(description='Internal Server Error'),
        },
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, *args, **kwargs):
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        # create metadata file content
        metadata_content = ''
        metadata_content += f'{artwork._meta.get_field("title").verbose_name.title()}: {artwork.title} \n'
        if len(artwork.artists.all()) > 1:
            metadata_content += f'{artwork._meta.get_field("artists").verbose_name.title()}: {[i.name for i in artwork.artists.all()]} \n'
        else:
            metadata_content += f'Artist: {artwork.artists.all()[0]} \n'
        metadata_content += (
            f'{artwork._meta.get_field("date").verbose_name.title()}: {artwork.date} \n'
        )
        metadata_content += f'{artwork._meta.get_field("material").verbose_name.title()}: {artwork.material} \n'
        metadata_content += f'{artwork._meta.get_field("dimensions").verbose_name.title()}: {artwork.dimensions} \n'
        metadata_content += f'{artwork._meta.get_field("description").verbose_name.title()}: {artwork.description} \n'
        metadata_content += f'{artwork._meta.get_field("credits").verbose_name.title()}: {artwork.credits} \n'
        metadata_content += f'{artwork._meta.get_field("keywords").verbose_name.title()}: {[i.name for i in artwork.keywords.all()]} \n'
        metadata_content += f'{artwork._meta.get_field("location").verbose_name.title()}: {artwork.location if artwork.location else ""} \n'
        metadata_content += f'{artwork._meta.get_field("place_of_production").verbose_name.title()}: {artwork.place_of_production} \n'

        output_zip = BytesIO()

        #  image to zipfile & metadata
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as image_zip:
            artwork_title = slugify(artwork.title)
            image_suffix = artwork.image_original.name.split('.')[-1]

            try:
                image_zip.write(
                    artwork.image_original.path,
                    arcname=f'{artwork_title}.{image_suffix}',
                )
            except FileNotFoundError:
                error_info = _('File for artwork {pk} not found')
                logger.exception(error_info.format(pk=pk))
                return Response(
                    error_info.format(pk=pk),
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            image_zip.writestr(f'{artwork_title}_metadata.txt', metadata_content)
            image_zip.close()

            return HttpResponse(
                output_zip.getvalue(),
                content_type='application/x-zip-compressed',
                headers={
                    'Content-Disposition': f'attachment; filename={artwork_title}.zip',
                },
            )


def filter_title(filter_values):
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(title__unaccent__icontains=val) | Q(
                title_english__unaccent__icontains=val
            )
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects &= Q(pk=val.get('id'))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for title filter.')
            )

    return q_objects


def filter_artists(filter_values):
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(artists__name__unaccent__icontains=val)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects &= Q(artists__id=val.get('id'))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for artists filter.')
            )

    return q_objects


def filter_mptt_model(filter_values, model, search_field):
    """Helper function for other filters, to filter a MPTT model based
    field."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(**{f'{search_field}__name__unaccent__icontains': val})
        elif isinstance(val, dict) and 'id' in val.keys():
            entries = model.objects.filter(pk=val.get('id')).get_descendants(
                include_self=True
            )
            q_objects &= Q(**{f'{search_field}__in': entries})
        else:
            raise ParseError(
                f'Invalid format of at least one filter_value for {search_field} filter.'
            )

    return q_objects


def filter_place_of_production(filter_values):
    return filter_mptt_model(filter_values, Location, 'place_of_production')


def filter_location(filter_values):
    return filter_mptt_model(filter_values, Location, 'location')


def filter_keywords(filter_values):
    return filter_mptt_model(filter_values, Keyword, 'keywords')


def filter_date(filter_values):
    if not isinstance(filter_values, dict) or (
        'date_from' not in filter_values and 'date_to' not in filter_values
    ):
        raise ParseError(_('Invalid filter_value format for date filter.'))

    date_from = filter_values.get('date_from')
    date_to = filter_values.get('date_to')
    if not date_from and not date_to:
        raise ParseError(_('Invalid filter_value format for date filter.'))
    try:
        if date_from:
            date_from = int(date_from)
        if date_to:
            date_to = int(date_to)
    except ValueError as err:
        raise ParseError(
            _('Invalid format of at least one filter_value for date filter.')
        ) from err

    if date_from and date_to and date_to < date_from:
        raise ParseError(_('date_from needs to be less than or equal to date_to.'))

    # in case only date_from is provided, all dates in its future should be found
    if not date_to:
        return Q(date_year_from__gte=date_from) | Q(date_year_to__gte=date_from)
    # in case only date_to is provided, all dates past this date should be found
    elif not date_from:
        return Q(date_year_from__lte=date_to) | Q(date_year_to__lte=date_to)
    # if both parameters are provided, we search within the given date range
    else:
        return (
            Q(date_year_from__range=[date_from, date_to])
            | Q(date_year_to__range=[date_from, date_to])
            | Q(
                date_year_from__lte=date_from,
                date_year_to__gte=date_to,
            )
        )


def featured_artworks(album, request, num_artworks=4):
    artworks = []

    for slide in album.slides:
        for item in slide:
            try:
                artwork = Artwork.objects.get(id=item['id'])
            except Artwork.DoesNotExist as dne:
                raise NotFound(_('Artwork does not exist')) from dne

            artworks.append(
                {
                    'id': artwork.pk,
                    'image_original': request.build_absolute_uri(
                        artwork.image_original.url
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                }
            )

            if len(artworks) == num_artworks:
                return artworks

    return artworks


@extend_schema(tags=['albums'])
class AlbumsViewSet(viewsets.ViewSet):
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
        # Albums and Folders sorting fields differ
        if sorting == 'date_created' or sorting == '-date_created':
            sorting = 'created_at' if '-' not in sorting else '-created_at'

        if sorting == 'date_changed' or sorting == '-date_changed':
            sorting = 'updated_at' if '-' not in sorting else '-updated_at'

        q_filters = Q()

        if serializer.validated_data['owner']:
            q_filters |= Q(user=request.user)

        permissions = serializer.validated_data['permissions'].split(',')

        if permissions:
            q_filters |= Q(
                pk__in=PermissionsRelation.objects.filter(
                    user=request.user,
                    permissions__in=permissions,
                ).values_list('album__pk', flat=True)
            )

        albums = Album.objects.filter(q_filters).order_by(sorting)

        total = albums.count()

        albums = albums[offset : offset + limit]

        return Response(
            {
                'total': total,
                'results': [
                    {
                        'id': album.id,
                        'title': album.title,
                        'number_of_artworks': album.size(),
                        'featured_artworks': featured_artworks(album, request),
                        'owner': {
                            'id': album.user.username,
                            'name': album.user.get_full_name(),
                        },
                        'permissions': [
                            {
                                'user': {
                                    'id': p.user.username,
                                    'name': p.user.get_full_name(),
                                },
                                'permissions': [{'id': p.permissions}],
                            }
                            for p in PermissionsRelation.objects.filter(
                                album=album
                            ).filter(
                                **{}
                                if album.user == request.user
                                else {'user': request.user}
                            )
                        ],
                    }
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


class FoldersViewSet(viewsets.ViewSet):
    """
    list:
    GET /folders/
    List of all the user's folders (in anticipation that there will be folders later)

    create: # Note: to be implemented
    POST /folders/
    Create a new folder

    retrieve:
    GET /folders/<id>/
    Get folder with given id if it belongs to the user;
    if folder_id == 'root', return the content of the root folder for the current user
    """

    serializer_class = FolderSerializer
    queryset = Folder.objects.all()

    ordering_fields = ['title', 'date_created', 'date_changed']

    def get_album_in_folder_data(self, albums, request):
        return [
            {
                'id': album.id,
                'title': album.title,
                'type': album._meta.object_name,
                'number_of_artworks': album.size(),
                'featured_artworks': featured_artworks(album, request),
                'owner': {
                    'id': album.user.username,
                    'name': album.user.get_full_name(),
                },
                'permissions': [
                    {
                        'user': {
                            'id': p.user.username,
                            'name': p.user.get_full_name(),
                        },
                        'permissions': [{'id': p.permissions}],
                    }
                    for p in PermissionsRelation.objects.filter(album=album).filter(
                        **{} if album.user == request.user else {'user': request.user}
                    )
                ],
            }
            for album in albums
        ]

    @extend_schema(
        tags=['folders'],
        request=FolderSerializer,
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
        """List of all the users albums /folders (in anticipation that there
        will be folders later)"""

        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))
        sorting = check_sorting(
            request.query_params.get('sort_by', 'title'), self.ordering_fields
        )

        results = self.queryset.filter(owner=request.user).order_by(sorting)
        results = results[offset : offset + limit]

        return Response(
            [
                {
                    'id': folder.id,
                    'title': folder.title,
                    'owner': f'{folder.owner.first_name} {folder.owner.last_name}',
                }
                for folder in results
            ]
        )

    @extend_schema(
        tags=['folders'],
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
                    'If the response should also return shared albums, it\'s possible to define which permissions the '
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
    def retrieve(self, request, *args, **kwargs):
        """Get folder with given id if it belongs to the user; if folder_id ==
        'root', return the content of the root folder for the current user."""
        folder_id = kwargs['pk']

        serializer = FoldersRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))
        sorting = check_sorting(
            request.query_params.get('sort_by', 'title'), self.ordering_fields
        )
        permissions = request.query_params.get('permissions', 'EDIT')

        # Albums sorting fields differ, but we want to be coherent in the request so here is a hacky adaptation
        if sorting == 'date_created' or sorting == '-date_created':
            sorting = 'created_at' if '-' not in sorting else '-created_at'

        if sorting == 'date_changed' or sorting == '-date_changed':
            sorting = 'updated_at' if '-' not in sorting else '-updated_at'

        # Retrieve folder by id
        if folder_id == 'root':
            folder = Folder.root_folder_for_user(request.user)
        else:
            # As we now only have root folder, this is not immediately useful
            # But I am leaving it here in case someone was searching something other than root
            try:
                folder = Folder.objects.get(owner=request.user, id=folder_id)
            except Folder.DoesNotExist as dne:
                raise NotFound(_('Folder does not exist')) from dne

        q_filters_albums = Q()

        # Permissions are only for Album for the moment
        if permissions:
            q_filters_albums |= Q(
                pk__in=PermissionsRelation.objects.filter(
                    user=request.user,
                    permissions__in=permissions,
                ).values_list('album__pk', flat=True)
            )

        if serializer.validated_data['owner']:
            q_filters_albums |= Q(user=serializer.validated_data['owner'])

        return Response(
            {
                'id': folder.id,
                'title': folder.title,
                'content': {
                    # Content shows all the albums belonging to the (root) folder per user.
                    # As at the moment we only have root folders, folders within folders
                    # will later be implemented to be shown in content (todo)
                    'total': sum(
                        [
                            folder.albums.all().count(),
                        ]
                    ),  # number of albums belonging to root folder
                    'data': [
                        self.get_album_in_folder_data(
                            list(
                                folder.albums.filter(q_filters_albums).order_by(sorting)
                            ),
                            request,
                        )
                    ][offset : offset + limit],
                },
            }
        )

    @extend_schema(
        methods=['POST'],
        parameters=[
            OpenApiParameter(
                name='create_folder',
                type=OpenApiTypes.OBJECT,
                required=False,
                description='',
                examples=[
                    OpenApiExample(
                        name='create_folder',
                        value=[
                            {
                                'title': 'Some title',
                                'ID': 1111,
                                'shared_info': 'Some shared info',
                                '# of works': 89,
                                'thumbnail': 'https://www.thumbnail.com',
                            }
                        ],
                    )
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def create_folder(self, request, *args, **kwargs):
        """Create Folder /albums/{id}"""
        # Note: this is a placeholder
        # todo
        # Create folder with given data
        # validate object
        # check for user.username compatibility

        dummy_data = {
            'title': request.data.get('title'),
            'ID': 1111,
            'shared_info': 'Some shared info',
            '# of works': 89,
            'thumbnail': 'https://www.thumbnail.com',
        }
        # Todo: update response
        return Response(dummy_data)


@extend_schema(tags=['labels'])
class LabelsViewSet(viewsets.GenericViewSet):
    """
    list:
    GET labels
    """

    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        ret = {}

        exclude = (
            'id',
            'created_at',
            'updated_at',
            'checked',
            'published',
        )

        # Artworks
        fields = Artwork._meta.get_fields()
        for field in fields:
            if field.name not in exclude and hasattr(field, 'verbose_name'):
                ret[field.name] = field.verbose_name

        return Response(ret)


@extend_schema(tags=['permissions'])
class PermissionsViewSet(viewsets.GenericViewSet):
    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    def list(self, request, *args, **kwargs):
        ret = []
        for permission_type in PermissionsRelation.PERMISSION_CHOICES:
            permission = {
                'id': permission_type[0],
                'label': permission_type[1],
            }
            if permission_type[0] in settings.DEFAULT_PERMISSIONS:
                permission['default'] = True
            ret.append(permission)
        return Response(ret)


@extend_schema(
    tags=['user'],
    responses={
        200: UserDataSerializer,
        401: ERROR_RESPONSES[401],
    },
)
@api_view(['GET'])
def get_user_data(request, *args, **kwargs):
    attributes = request.session.get('attributes', {})
    ret = {
        'id': request.user.username,
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'showroom_id': attributes.get('showroom_id'),
        'groups': attributes.get('groups'),
        'permissions': attributes.get('permissions'),
    }
    return Response(ret, status=200)


FILTERS_MAP = {}
for filter_id in FILTERS_KEYS:
    FILTERS_MAP[filter_id] = globals()[f'filter_{filter_id}']


@extend_schema(
    tags=['search'],
    request=SearchRequestSerializer,
    examples=[
        OpenApiExample(
            name='search with filter type title, artist, place_of_production, current_location, keywords',
            value={
                'limit': settings.SEARCH_LIMIT,
                'offset': 0,
                'exclude': [123, 345],  # with artwork ids
                'q': 'query string',  # the string from general search
                'filters': [
                    {
                        'id': 'artists',
                        'filter_values': ['lassnig', {'id': 1192}],
                    }
                ],
            },
        ),
        OpenApiExample(
            name='search with filter type date',
            value={
                'limit': settings.SEARCH_LIMIT,
                'offset': 0,
                'exclude': [123, 345],  # with artwork ids
                'q': 'query string',  # the string from general search
                'filters': [
                    {
                        'id': 'date',
                        'filter_values': {
                            'date_from': '2000',
                            'date_to': '2001',
                        },
                    }
                ],
            },
        ),
    ],
    responses={
        200: SearchResultSerializer,
        403: ERROR_RESPONSES[403],
        404: ERROR_RESPONSES[404],
    },
)
@api_view(['post'])
def search(request, *args, **kwargs):
    serializer = SearchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    limit = check_limit(serializer.validated_data.get('limit'))
    offset = check_offset(serializer.validated_data.get('offset'))
    filters = serializer.validated_data.get('filters', [])
    q_param = serializer.validated_data.get('q')
    exclude = serializer.validated_data.get('exclude', [])

    if q_param:
        qs = Artwork.objects.search(q_param).annotate(total_results=Window(Count('pk')))
    else:
        qs = Artwork.objects.annotate(rank=Value(1.0, FloatField())).annotate(
            total_results=Window(Count('pk'))
        )
        if filters:
            qs = qs.order_by('title')
        else:
            # user is not using search at all, therefor show the newest changes first
            qs = qs.order_by('-updated_at', 'title')

    # only search for published artworks
    qs = qs.filter(published=True)

    qs = qs.prefetch_related('artists')

    if exclude:
        qs = qs.exclude(id__in=exclude)

    if filters:
        q_objects = Q()

        for f in filters:
            if f['id'] not in FILTERS_KEYS:
                raise ParseError(f'Invalid filter id {repr(f["id"])}')

            q_objects &= FILTERS_MAP[f['id']](f['filter_values'])

        qs = qs.filter(q_objects).distinct()

    qs = qs[offset : offset + limit]

    total = 0
    results = []

    for artwork in qs:
        # for performance reasons we get the total results count via annotation
        # annotate(total_results=Window(Count('pk')))
        # and for convenience reasons we just set it in every for loop
        # iteration even though the value is the same for all results
        total = artwork.total_results

        results.append(
            {
                'id': artwork.id,
                'image_original': request.build_absolute_uri(artwork.image_original.url)
                if artwork.image_original
                else None,
                'credits': artwork.credits,
                'title': artwork.title,
                'date': artwork.date,
                'artists': [
                    {'value': artist.name, 'id': artist.id}
                    for artist in artwork.artists.all()
                ],
                'score': artwork.rank,
            }
        )

    return Response({'total': total, 'results': results})


@extend_schema(
    tags=['search'],
    responses={
        200: inline_serializer(
            name='SearchFiltersResponse',
            fields={k: JSONField() for k in FILTERS_KEYS},
        ),
        403: ERROR_RESPONSES[403],
        404: ERROR_RESPONSES[404],
    },
)
@api_view(['get'])
def search_filters(request, *args, **kwargs):
    return Response(FILTERS)


@extend_schema(
    tags=['labels'],
    responses={
        200: OpenApiResponse(
            description='A list of discriminatory terms, which should be contextualised.',
        ),
    },
)
@api_view(['get'])
def discriminatory_terms(request, *args, **kwargs):
    return Response(list(DiscriminatoryTerm.objects.values_list('term', flat=True)))
