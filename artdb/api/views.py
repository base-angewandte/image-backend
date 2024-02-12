import logging
import re
import zipfile
from io import BytesIO

from artworks.exports import (
    collection_download_as_pptx_de,
    collection_download_as_pptx_en,
)
from artworks.models import Album, Artwork, Keyword, Location, PermissionsRelation
from base_common_drf.openapi.responses import ERROR_RESPONSES
from django_filters.rest_framework import DjangoFilterBackend
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
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response
from rest_framework.serializers import JSONField

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import FloatField, Q, Value
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .search.filters import FILTERS, FILTERS_KEYS
from .serializers import (
    AlbumSerializer,
    AlbumsRequestSerializer,
    CreateAlbumRequestSerializer,
    PermissionsRequestSerializer,
    PermissionsResponseSerializer,
    SearchRequestSerializer,
    SearchResultSerializer,
    SlidesSerializer,
    UpdateAlbumRequestSerializer,
    UserDataSerializer,
)

logger = logging.getLogger(__name__)


def artworks_in_slides(album):
    info_per_slide = []
    if album.slides:
        for slide in album.slides:
            artwork_info = []
            for artwork_in_slide in slide:
                try:
                    artwork = Artwork.objects.get(id=artwork_in_slide.get('id'))
                except Artwork.DoesNotExist:
                    return Response(
                        _(
                            f'There is no artwork associated with id {artwork_in_slide.get("id")}.'
                        ),
                        status=status.HTTP_404_NOT_FOUND,
                    )

                artwork_info.append(
                    {
                        'id': artwork.id,
                        'image_original': f'{settings.SITE_URL}{Artwork.objects.get(id=artwork.id).image_original}'
                        if Artwork.objects.get(id=artwork.id).image_original
                        else None,
                        'credits': artwork.credits,
                        'title': artwork.title,
                        'date': artwork.date,
                        'artists': [
                            {'value': artist.name, 'id': artist.id}
                            for artist in artwork.artists.all()
                        ],
                    }
                )
            info_per_slide.append(artwork_info)

    return info_per_slide


def simple_album_object(album):
    return Response(
        {
            'id': album.id,
            'title': album.title,
            'number_of_artworks': album.artworks.all().count(),
            'slides': [
                artwork_in_slide for artwork_in_slide in artworks_in_slides(album)
            ],
            'owner': {
                'id': album.user.id,
                'name': f'{album.user.first_name} {album.user.last_name}',
            },
            'permissions': [
                {
                    'user': {
                        'id': p.user.id,
                        'name': f'{p.user.first_name} {p.user.last_name}',
                    },
                    'permission': [
                        {'id': p.permissions}  # possible values: view | edit
                    ],
                }
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ],
        }
    )


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
    filter_backends = (DjangoFilterBackend,)

    @extend_schema(
        parameters=[
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
                default=0,
            ),
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        try:
            limit = int(request.query_params.get('limit', 100))
            if limit <= 0:
                raise ValueError
        except ValueError as e:
            raise ParseError(_('limit must be a positive integer')) from e

        try:
            offset = int(request.query_params.get('offset', 0))
            if offset < 0:
                raise ParseError(_('negative offset is not allowed'))
        except ValueError as e:
            raise ParseError(_('offset must be an integer')) from e

        results = self.get_queryset()

        total = results.count()

        results = results[offset : offset + limit]

        return Response(
            {
                'total': total,
                'results': [
                    {
                        'id': artwork.id,
                        'image_original': artwork.image_original.url
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

        return Response(
            {
                'id': artwork.id,
                'image_original': artwork.image_original.url
                if artwork.image_original
                else None,
                'credits': artwork.credits,
                'license': 'String',  # placeholder for future field change, see ticket 2070
                'title': artwork.title,
                'title_english': artwork.title_english,
                'title_notes': 'String',  # placeholder for future field change, see ticket 2070
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
                name='owner',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Boolean indicating to return albums owned by this user.',
                default=True,
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
                    'permissions are inculuded in the response.'
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
    @action(detail=True, methods=['get'], url_path='albums')
    def retrieve_albums(self, request, pk=None, *args, **kwargs):
        serializer = AlbumsRequestSerializer(data=request.query_params)
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
            # create zip file

            try:
                image_zip.write(
                    artwork.image_original.path,
                    arcname=artwork.image_original.name,
                )
            except FileNotFoundError:
                error_info = _('File for artwork {pk} not found')
                logger.exception(error_info.format(pk=pk))
                return Response(
                    error_info.format(pk=pk),
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            artwork_title = slugify(artwork.title)

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
    """Should filter artworks whose title include the string if given, AND the
    artworks with given id."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects |= Q(title__icontains=val) | Q(title_english__icontains=val)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(id=val.get('id'))
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.',
                400,
            )

    return q_objects


def filter_artists(filter_values):
    """Should filter artworks whose artist name includes the string if given,
    AND the artworks for artist which has the given id."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(artists__id=val.get('id'))

        if isinstance(val, str):
            terms = val.split(' ')
            for term in terms:
                q_objects |= Q(artists__name__unaccent__icontains=term)

    return q_objects


def filter_place_of_production(filter_values):
    """Should filter artworks whose place of production includes the string if
    given, AND the artworks for place of production which has the given id."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(place_of_production__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            location = Location.objects.filter(id=val.get('id'))
            location_plus_descendants = Location.objects.get_queryset_descendants(
                location,
                include_self=True,
            )
            q_objects |= Q(place_of_production__in=location_plus_descendants)
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.'
            )

    return q_objects


def filter_location(filter_values):
    """Should filter artworks whose location includes the string if given, AND
    the artworks for location which has the given id."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(location__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            location = Location.objects.filter(id=val.get('id'))
            location_plus_descendants = Location.objects.get_queryset_descendants(
                location,
                include_self=True,
            )
            q_objects |= Q(location__in=location_plus_descendants)
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.'
            )

    return q_objects


def filter_keywords(filter_values):
    """Should filter artworks whose keywords include the string if given, AND
    the artworks for keyword which has the given id."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            keywords = Keyword.objects.filter(name__icontains=val)
            q_objects |= Q(keywords__in=keywords)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(keywords__id=val.get('id'))
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.',
                400,
            )

    return q_objects


def filter_date(filter_values):
    q_objects = Q()
    if isinstance(filter_values, dict):
        if re.match(r'^[12][0-9]{3}$', filter_values.get('date_from')):
            q_objects |= Q(date_year_from__gte=filter_values['date_from'])
        if re.match(r'^[12][0-9]{3}$', filter_values.get('date_to')):
            q_objects |= Q(date_year_to__lte=filter_values['date_to'])
        else:
            raise ParseError(
                'Only dates of format YYYY can be used as date filter values',
                400,
            )

    else:
        return Response(
            _('Invalid filter_value format. See example below for more information.')
        )

    return q_objects


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
    filter_backends = (DjangoFilterBackend,)

    @extend_schema(
        request=AlbumSerializer,
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                description='',
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
        """List of all Albums (used for getting latest Albums) /albums."""
        limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
        offset = int(request.GET.get('offset')) if request.GET.get('offset') else None

        results = Album.objects.all()

        slides_ids = []

        for album in results:
            if album.slides:
                for artworks_list in album.slides:
                    for slides in artworks_list:
                        if Artwork.objects.filter(id=slides.get('id')).first():
                            slides_ids.append(slides.get('id'))

        total = len(results)

        limit = limit if limit != 0 else None

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        results = results[offset:end]

        return Response(
            {
                'total': total,
                'results': [
                    {
                        'id': album.id,
                        'title': album.title,
                        'number_of_artworks': album.artworks.all().count(),  # number of artworks in a specific album
                        'artworks': [
                            # the first 4 artworks from all slides: [[{"id":1}], [2,3], [4,5]] -> 1,2,3,4,max 4 objects
                            {
                                'id': artwork_id,
                                'image_original': f'{settings.SITE_URL}{Artwork.objects.get(id=artwork_id).image_original}'
                                if Artwork.objects.get(id=artwork_id).image_original
                                else None,
                                'title': Artwork.objects.get(id=artwork_id).title,
                            }
                            for artwork_id in slides_ids
                            if artwork_id
                        ][:4]
                        if album.slides
                        else [],
                        'owner': {
                            'id': album.user.id,
                            'name': f'{album.user.first_name} {album.user.last_name}',
                        },
                        'permissions': [
                            {
                                'user': {
                                    'id': p.user.id,
                                    'name': f'{p.user.first_name} {p.user.last_name}',
                                },
                                'permission': [
                                    {
                                        'id': p.permissions  # possible values: view | edit
                                    }
                                ],
                            }
                            for p in PermissionsRelation.objects.filter(
                                album__id=album.id
                            )
                        ],
                    }
                    for album in results
                    if (album.user.username == request.user.username)
                    or (
                        request.user.username
                        in [
                            p.user.username
                            for p in PermissionsRelation.objects.filter(
                                album__id=album.id
                            )
                        ]
                        and 'VIEW'
                        in [
                            p.permissions
                            for p in PermissionsRelation.objects.filter(
                                user__username=request.user.username
                            )
                        ]
                    )
                ],
            }
        )

    @extend_schema(
        request=CreateAlbumRequestSerializer,
        responses={201: AlbumSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Create Album /albums/{id}"""
        serializer = CreateAlbumRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data['title']

        album = Album.objects.create(title=title, user=request.user)

        resp = simple_album_object(album)
        resp.status_code = status.HTTP_201_CREATED
        return resp

    @extend_schema(
        request=AlbumSerializer,
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, pk=None, *args, **kwargs):  # TODO update
        """List of Works (Slides) in a specific Album /albums/{id}"""

        album_id = pk
        try:
            album = Album.objects.get(pk=album_id)
            if album.user.username == request.user.username:
                return simple_album_object(album)
            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'VIEW' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                return simple_album_object(album)
            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)
        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=UpdateAlbumRequestSerializer,
        responses={
            200: AlbumSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def update(self, request, pk=None, *args, **kwargs):
        """Update Album /albums/{id}"""
        album_id = pk

        try:
            album = Album.objects.get(pk=album_id)
            album.title = request.data.get('title')

            serializer = UpdateAlbumRequestSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            if album.user.username == request.user.username:
                album.save()
                return simple_album_object(album)

            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'EDIT' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                album.save()
                return simple_album_object(album)

            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)

        except Album.DoesNotExist:
            return Response(
                _('Album does not exist '),
                status=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, pk=None, *args, **kwargs):
        """Delete Album /albums/{id}"""
        album_id = pk
        try:
            album = Album.objects.get(pk=album_id)
            if album.user.username == request.user.username:
                album.delete()
                return Response(
                    _('Album {album_title} was deleted').format(
                        album_title=album.title
                    ),
                    status=status.HTTP_200_OK,
                )

            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'EDIT' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                album.delete()
                return Response(
                    _('Album {album_title} was deleted').format(
                        album_title=album.title
                    ),
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)
        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

    # additional actions

    @extend_schema(
        responses={
            200: AlbumSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['post'], url_path='append-artwork')
    def append_artwork(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/append_artwork Append artwork to slides as singular
        slide [{'id': x}]"""

        album_id = pk
        try:
            album = Album.objects.get(pk=album_id)
            if not album.slides:
                album.slides = []

            # Check if artwork exists
            artwork = Artwork.objects.get(pk=int(request.GET.get('artwork_id')))

            album.slides.append([{'id': artwork.id}])
            if album.user.username == request.user.username:
                album.save()
                return Response(_('Artwork added.'), status=status.HTTP_200_OK)
            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'EDIT' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                album.save()
                return Response(_('Artwork added.'), status=status.HTTP_200_OK)
            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)

        except Artwork.DoesNotExist:
            return Response(
                _('There is no artwork associated with the given id.'),
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'])
    def slides(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/slides LIST (GET) endpoint returns:"""
        album_id = pk
        try:
            album = Album.objects.get(pk=album_id)
        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        if album.user.username == request.user.username:
            return Response(artworks_in_slides(album))
        if request.user.username in [
            p.user.username
            for p in PermissionsRelation.objects.filter(album__id=album.id)
        ] and 'VIEW' in [
            p.permissions
            for p in PermissionsRelation.objects.filter(
                user__username=request.user.username
            )
        ]:
            return Response(artworks_in_slides(album))
        else:
            return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)

    @extend_schema(
        request=SlidesSerializer,
        examples=[
            OpenApiExample(
                name='slides',
                value=[[{'id': 123}, {'id': 456}], [{'id': 789}], [{'id': 123}]],
            )
        ],
        responses={
            200: AlbumSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @slides.mapping.post
    def create_slides(self, request, pk=None, *args, **kwargs):
        """/albums/{id}/slides Reorder Slides, Separate_slides, Reorder
        artworks within slides."""

        album_id = pk
        try:
            album = Album.objects.get(pk=album_id)
            slides_serializer = SlidesSerializer(data=request.data)

            # Validate slides object
            if not slides_serializer.is_valid():
                return Response(
                    _('Slides format incorrect'), status=status.HTTP_400_BAD_REQUEST
                )

            slides = slides_serializer.data.get('slides')

            # Check if artworks exist
            artworks = []
            for artworks_list in slides:
                for slide in artworks_list:
                    if len(artworks_list) <= 2:
                        try:
                            artworks.append(Artwork.objects.get(id=slide.get('id')))
                        except Artwork.DoesNotExist:
                            return Response(
                                _(
                                    f'There is no artwork associated with id {slide.get("id")}.'
                                ),
                                status=status.HTTP_404_NOT_FOUND,
                            )
                    else:
                        return Response(
                            _('No more than two artworks per slide.'),
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            album.slides = slides

            if album.user.username == request.user.username:
                album.save()
                return Response(artworks_in_slides(album))
            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'EDIT' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                album.save()
                return Response(artworks_in_slides(album))

            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)

        except TypeError as e:
            return Response(
                _('Could not edit slides: {e}').format(e=e),
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        responses={
            200: PermissionsResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None, *args, **kwargs):
        """Get Permissions /albums/{id}/permissions."""
        try:
            album = (
                Album.objects.filter(pk=pk)
                .filter(Q(user=request.user) | Q(permissions=request.user))
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        qs = PermissionsRelation.objects.filter(album=album)

        # if the user is not the owner of the album, ony return the permissions of this user
        if album.user != request.user:
            qs = qs.filter(user=request.user)

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
        request=PermissionsRequestSerializer(many=True),
        examples=[
            OpenApiExample(
                name='shared_info',
                value=[{'user': 'username', 'permissions': {'id': 'VIEW'}}],
            )
        ],
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
                PermissionsRelation.objects.update_or_create(
                    album=album,
                    user=user,
                    permissions=perm['id'],
                )

        # remove deleted permissions
        PermissionsRelation.objects.filter(album=album).exclude(
            user__username__in=users
        ).delete()

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
                .get()
            )
        except Album.DoesNotExist as dne:
            raise NotFound(_('Album does not exist')) from dne

        # user is owner of the album
        if album.user == request.user:
            PermissionsRelation.objects.filter(album=album).delete()

        # album is shared with user
        else:
            PermissionsRelation.objects.filter(album=album, user=request.user).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='language',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                enum=['de', 'en'],
                default='en',
                description='de or en. The default value is en',
            ),
            OpenApiParameter(
                name='download_format',
                type=OpenApiTypes.STR,
                enum=['pptx', 'pdf'],  # Todo: PDF will be made functional later
                default='pptx',
                description="At the moment, only 'pptx' is available. Later on, 'PDF' will also be available",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
            501: OpenApiResponse(description='Not implemented yet'),
        },
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, *args, **kwargs):
        # Todo: now only pptx, later also PDF
        album_id = pk
        try:
            album = Album.objects.get(id=album_id)
            # If user is the owner or has VIEW permissions, allow the download. Otherwise, throw a 403
            if (album.user.username == request.user.username) or (
                request.user.username
                in [
                    p.user.username
                    for p in PermissionsRelation.objects.filter(album__id=album.id)
                ]
                and 'VIEW'
                in [
                    p.permissions
                    for p in PermissionsRelation.objects.filter(
                        user__username=request.user.username
                    )
                ]
            ):
                download_format = request.GET.get('download_format')
                lang = request.headers.get('Language')

                if download_format == 'pptx' and lang == 'en':
                    return collection_download_as_pptx_en(request, id=album_id)
                if download_format == 'pptx' and lang == 'de':
                    return collection_download_as_pptx_de(request, id=album_id)
                if download_format == 'pdf' and lang == 'en':
                    # Todo to implement
                    return Response(
                        _('Not implemented yet'),
                        status.HTTP_501_NOT_IMPLEMENTED,
                    )
                if download_format == 'pdf' and lang == 'de':
                    # Todo to implement
                    return Response(
                        _('Not implemented yet'),
                        status.HTTP_501_NOT_IMPLEMENTED,
                    )
                return Response(_('Wrong parameters.'), status.HTTP_400_BAD_REQUEST)

            return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)
        except Album.DoesNotExist:
            return Response(_("Album doesn't exist"), status.HTTP_404_NOT_FOUND)


@extend_schema(tags=['labels'])
class LabelsViewSet(viewsets.GenericViewSet):
    """
    list:
    GET labels
    """

    @extend_schema(
        responses={
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
    request={'application/json': SearchRequestSerializer},
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
                        'id': 'artist',
                        'filter_values': ['rubens', {'id': 786}],
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

    limit = serializer.validated_data.get('limit', settings.SEARCH_LIMIT)
    offset = serializer.validated_data.get('offset', 0)
    filters = serializer.validated_data.get('filters', [])
    q_param = serializer.validated_data.get('q')
    exclude = serializer.validated_data.get('exclude', [])

    if q_param:
        qs = Artwork.objects.search(q_param)
    else:
        qs = Artwork.objects.annotate(rank=Value(1.0, FloatField()))

    # only search for published artworks
    qs = qs.filter(published=True)

    if exclude:
        qs = qs.exclude(id__in=exclude)

    if filters:
        q_objects = Q()

        for f in filters:
            if f['id'] not in FILTERS_KEYS:
                raise ParseError(f'Invalid filter id {repr(f["id"])}')

            q_objects |= FILTERS_MAP[f['id']](f['filter_values'])

        qs = qs.filter(q_objects)

    # total of results before applying limits
    total = qs.count()

    qs = qs[offset : offset + limit]

    return Response(
        {
            'total': total,
            'results': [
                {
                    'id': artwork.id,
                    'image_original': artwork.image_original.url
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
                for artwork in qs
            ],
        }
    )


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
