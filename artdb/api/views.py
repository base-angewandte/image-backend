import json
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
)
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .serializers import (
    AlbumSerializer,
    CreateAlbumSerializer,
    PermissionsSerializer,
    SearchRequestSerializer,
    SearchResponseSerializer,
    SlidesSerializer,
    UpdateAlbumSerializer,
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


def simple_album_object(album, request):
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

    search:
    GET artworks according to search parameters.

    list_search_filters:
    GET filters for search.

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
            limit = (
                int(request.GET.get('limit'))
                if request.GET.get('limit')
                else 100  # default limit
            )
            offset = (
                int(request.GET.get('offset')) if request.GET.get('offset') else None
            )
        except ValueError:
            return Response('Limit and offset should be int')

        results = self.get_queryset()

        limit = limit if limit != 0 else None

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        total = results.count()
        results = results[offset:end]

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
    def retrieve(self, request, *args, **kwargs):
        item_id = kwargs['id']
        try:
            artwork = self.get_queryset().get(pk=item_id)
        except Artwork.DoesNotExist:
            return Response(
                _('Artwork does not exist'),
                status=status.HTTP_404_NOT_FOUND,
            )

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
                'location_of_creation': {
                    'id': artwork.location_of_creation.id,
                    'value': artwork.location_of_creation.name,
                }
                if artwork.location_of_creation
                else {},
                'location_current': {
                    'id': artwork.location_current.id,
                    'value': artwork.location_current.name,
                }
                if artwork.location_current
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
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'], url_path='albums')
    def retrieve_albums(self, request, *args, **kwargs):
        item_id = kwargs['id']
        try:
            artwork = Artwork.objects.get(pk=item_id)
            albums = Album.objects.filter(slides__contains=[[{'id': artwork.pk}]])
        except Artwork.DoesNotExist:
            return Response(
                _('Artwork does not exist'),
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            [
                {
                    'id': album.id,
                    'value': album.title,
                }
                for album in albums
                if (album.user.username == request.user.username)
                or (
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
                )
            ]
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'])
    def download(self, request, *args, **kwargs):
        artwork_id = kwargs['id']
        try:
            artwork = Artwork.objects.get(id=artwork_id)

            output_zip = BytesIO()

            # create metadata file
            artwork_title = slugify(artwork.title)

            metadata_content = ''
            metadata_content += f'{artwork._meta.get_field("title").verbose_name.title()}: {artwork.title} \n'
            if len(artwork.artists.all()) > 1:
                metadata_content += f'{artwork._meta.get_field("artists").verbose_name.title()}: {[i.name for i in artwork.artists.all()]} \n'
            else:
                metadata_content += f'Artist: {artwork.artists.all()[0]} \n'
            metadata_content += f'{artwork._meta.get_field("date").verbose_name.title()}: {artwork.date} \n'
            metadata_content += f'{artwork._meta.get_field("material").verbose_name.title()}: {artwork.material} \n'
            metadata_content += f'{artwork._meta.get_field("dimensions").verbose_name.title()}: {artwork.dimensions} \n'
            metadata_content += f'{artwork._meta.get_field("description").verbose_name.title()}: {artwork.description} \n'
            metadata_content += f'{artwork._meta.get_field("credits").verbose_name.title()}: {artwork.credits} \n'
            metadata_content += f'{artwork._meta.get_field("keywords").verbose_name.title()}: {[i.name for i in artwork.keywords.all()]} \n'
            metadata_content += f'{artwork._meta.get_field("location_current").verbose_name.title()}: {artwork.location_current if artwork.location_current else ""} \n'
            metadata_content += f'{artwork._meta.get_field("location_of_creation").verbose_name.title()}: {artwork.location_of_creation} \n'

            #  image to zipfile & metadata
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as image_zip:
                # create zip file

                image_zip.write(
                    artwork.image_original.path,
                    arcname=artwork.image_original.name,
                )
                image_zip.writestr(f'{artwork_title}_metadata.txt', metadata_content)
                image_zip.close()

                response = HttpResponse(
                    output_zip.getvalue(),
                    content_type='application/x-zip-compressed',
                )
                response[
                    'Content-Disposition'
                ] = f'attachment; filename={artwork_title}.zip'

                return response

        except Artwork.DoesNotExist:
            return Response(_("Artwork doesn't exist"), status.HTTP_404_NOT_FOUND)

        except FileNotFoundError:
            logger.error(f'File for id {artwork_id} not found')
            return Response(
                _(f'File for id {artwork_id} not found'), status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=['search'],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list_search_filters(self, request, *args, **kwargs):
        data = {
            'title': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'source': {'type': 'string'},
                    },
                },
                'title': 'title',
                'x-attrs': {
                    'field_format': 'half',
                    'field_type': 'chips',
                    'dynamic_autosuggest': True,
                    'allow_unknown_entries': True,
                    'source': '/autosuggest/v1/titles/',
                    'placeholder': 'enter title',
                    'order': 1,
                },
            },
            'artist': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'source': {'type': 'string'},
                    },
                },
                'title': 'artist',
                'x-attrs': {
                    'field_format': 'half',
                    'field_type': 'chips',
                    'dynamic_autosuggest': True,
                    'allow_unknown_entries': True,
                    'source': '/autosuggest/v1/artists/',
                    'placeholder': 'enter artist',
                    'order': 2,
                },
            },
            'place_of_production': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'source': {'type': 'string'},
                    },
                },
                'title': 'place of production',
                'x-attrs': {
                    'field_format': 'half',
                    'field_type': 'chips',
                    'dynamic_autosuggest': True,
                    'allow_unknown_entries': True,
                    'source': '/autosuggest/v1/locations/',
                    'placeholder': 'enter place of production',
                    'order': 3,
                },
            },
            'current_location': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'source': {'type': 'string'},
                    },
                },
                'title': 'current location',
                'x-attrs': {
                    'field_format': 'half',
                    'field_type': 'chips',
                    'dynamic_autosuggest': True,
                    'allow_unknown_entries': True,
                    'source': '/autosuggest/v1/locations/',
                    'placeholder': 'enter current location',
                    'order': 4,
                },
            },
            'keywords': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'source': {'type': 'string'},
                    },
                },
                'title': 'keywords',
                'x-attrs': {
                    'placeholder': 'enter keywords',
                    'order': 5,
                    'field_format': 'full',
                    'field_type': 'chips',
                    'allow_unknown_entries': False,
                    'dynamic_autosuggest': True,
                    'source': '/autosuggest/v1/keywords/',
                },
            },
            'date': {
                'type': 'object',
                'properties': {
                    'date_from': {'type': 'string'},
                    'date_to': {'type': 'string'},
                },
                'title': 'date from, to',
                'additionalProperties': False,
                'x-attrs': {
                    'field_format': 'full',
                    'field_type': 'date',
                    'date_format': 'year',
                    'placeholder': {'date': 'enter date'},
                    'order': 6,
                },
            },
        }

        return Response(data)

    @extend_schema(
        tags=['search'],
        methods=['POST'],
        request=SearchRequestSerializer,
        examples=[
            OpenApiExample(
                name='search with filter type title, artist, place_of_production, current_location, keywords',
                value=[
                    {
                        'limit': 0,
                        'offset': 0,
                        'exclude': [123, 345],  # with artwork ids
                        'q': '',  # the string from general search
                        'filters': [
                            {
                                'id': 'artist',
                                'filter_values': ['rubens', {'id': 786}],
                            }
                        ],
                    }
                ],
            ),
            OpenApiExample(
                name='search with filter type date',
                value=[
                    {
                        'limit': 0,
                        'offset': 0,
                        'exclude': [123, 345],  # with artwork ids
                        'q': '',  # the string from general search
                        'filters': [
                            {
                                'id': 'date',
                                'filter_values': {
                                    'date_from': '2000',
                                    'date_to': '2001',
                                },
                            }
                        ],
                    }
                ],
            ),
        ],
        responses={
            200: SearchResponseSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def search(self, request, *args, **kwargs):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        search_req_data = serializer.data.get('search_request')[0]

        limit = search_req_data.get('limit') if search_req_data.get('limit') else None
        offset = (
            search_req_data.get('offset') if search_req_data.get('offset') else None
        )
        filters = search_req_data.get('filters', [])
        searchstr = search_req_data.get('q', '')
        excluded = search_req_data.get('exclude', [])

        results = (
            Artwork.objects.exclude(id__in=[str(i) for i in excluded])
            if excluded
            else Artwork.objects.all()
        )
        q_objects = Q()

        for i in filters:
            if i['id'] == 'title':
                q_objects |= filter_title(i['filter_values'], q_objects, results)

            elif i['id'] == 'artist':
                q_objects |= filter_artist(i['filter_values'], q_objects, results)

            elif i['id'] == 'place_of_production':
                q_objects |= filter_place_of_production(
                    i['filter_values'],
                    q_objects,
                    results,
                )

            elif i['id'] == 'current_location':
                q_objects |= filter_current_location(
                    i['filter_values'],
                    q_objects,
                    results,
                )

            elif i['id'] == 'keywords':
                q_objects |= filter_keywords(i['filter_values'], q_objects, results)

            elif i['id'] == 'date':
                q_objects |= filter_date(i['filter_values'], q_objects, results)

            else:
                raise ParseError(
                    'Invalid filter id. Filter id can only be title, artist, place_of_production, '
                    'current_location, keywords, or date.',
                    400,
                )

        results = results.filter(q_objects)

        results = results.annotate(
            search=SearchVector(
                'title',
                'title_english',
                'artists',
                'material',
                'dimensions',
                'description',
                'credits',
                'keywords',
                'location_of_creation',
                'location_current',
            ),
        )

        final_results = []

        search_terms = searchstr.split(' ')
        for term in search_terms:
            if term:
                # It filters as intended if we literally append to a list when adding further filtering.
                # Possibly improvable, q_objects and direct filtering did not work so far
                final_results.extend(
                    list(
                        results.filter(search__icontains=term)
                        .order_by('id')
                        .distinct('id')
                    )
                )

        if final_results:
            results = final_results
        else:
            results = results.order_by('id').distinct('id')

        # total of results before applying limits:
        total = len(results)

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
                        'id': artwork.id,
                        'image_original': [
                            artwork.image_original.url
                            if artwork.image_original
                            else None
                        ],
                        'credits': artwork.credits,
                        'title': artwork.title,
                        'date': artwork.date,
                        'artists': [
                            {'value': artist.name, 'id': artist.id}
                            for artist in artwork.artists.all()
                        ],
                    }
                    for artwork in results
                ],
            }
        )


def filter_title(filter_values, q_objects, results):
    """Should filter artworks whose title include the string if given, AND the
    artworks with given id."""
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


def filter_artist(filter_values, q_objects, results):
    """Should filter artworks whose artist name includes the string if given,
    AND the artworks for artist which has the given id."""
    for val in filter_values:
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(artists__id=val.get('id'))

        if isinstance(val, str):
            terms = val.split(' ')
            for term in terms:
                q_objects |= Q(artists__name__unaccent__icontains=term)

    return q_objects


def filter_place_of_production(filter_values, q_objects, results):
    """Should filter artworks whose place of production includes the string if
    given, AND the artworks for place of production which has the given id."""
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(location_of_creation__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(location_of_creation__id=val.get('id'))
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.',
                400,
            )

    return q_objects


def filter_current_location(filter_values, q_objects, results):
    """Should filter artworks whose current location includes the string if
    given, AND the artworks for current location which has the given id."""
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(location_current__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(location_current__id=val.get('id'))
        else:
            raise ParseError(
                'Invalid filter_value format. See example below for more information.',
                400,
            )

    return q_objects


def filter_keywords(filter_values, q_objects, results):
    """Should filter artworks whose keywords include the string if given, AND
    the artworks for keyword which has the given id."""
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


def filter_date(filter_values, q_objects, results):
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

    retrieve_slides:
    GET /albums/{id}/slides LIST (GET) endpoint

    create_slides:
    POST /albums/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

    retrieve_permissions:
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
        request=CreateAlbumSerializer,  # todo fix serializers
        responses={200: AlbumSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Create Album /albums/{id}"""
        try:
            title = request.data.get('title')
            album = Album.objects.create(title=title, user=request.user)

            album.save()

            return simple_album_object(album, request)
        except ValueError:
            return Response(
                _('Album user must be a user instance'),
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        request=AlbumSerializer,
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, *args, **kwargs):  # TODO update
        """List of Works (Slides) in a specific Album /albums/{id}"""

        album_id = kwargs['id']
        try:
            album = Album.objects.get(pk=album_id)
            if album.user.username == request.user.username:
                return simple_album_object(album, request)
            if request.user.username in [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album.id)
            ] and 'VIEW' in [
                p.permissions
                for p in PermissionsRelation.objects.filter(
                    user__username=request.user.username
                )
            ]:
                return simple_album_object(album, request)
            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)
        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=UpdateAlbumSerializer,
        responses={
            200: AlbumSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def update(self, request, *args, **kwargs):
        """Update Album /albums/{id}"""
        album_id = kwargs['id']

        try:
            album = Album.objects.get(pk=album_id)
            album.title = request.data.get('title')

            serializer = UpdateAlbumSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            if album.user.username == request.user.username:
                album.save()
                return simple_album_object(album, request)

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
                return simple_album_object(album, request)

            else:
                return Response(_('Not allowed'), status.HTTP_403_FORBIDDEN)

        except Album.DoesNotExist:
            return Response(
                _('Album does not exist '),
                status=status.HTTP_404_NOT_FOUND,
            )

    def destroy(self, request, *args, **kwargs):
        """Delete Album /albums/{id}"""
        album_id = kwargs['id']
        try:
            album = Album.objects.get(pk=album_id)
            if album.user.username == request.user.username:
                album.delete()
                return Response(
                    _(f'Album {album.title} was deleted'),
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
                    _(f'Album {album.title} was deleted'),
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
    def append_artwork(self, request, *args, **kwargs):
        """/albums/{id}/append_artwork Append artwork to slides as singular
        slide [{'id': x}]"""

        album_id = kwargs['id']
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
    @action(detail=True, methods=['get'], url_path='slides')
    def retrieve_slides(self, request, *args, **kwargs):
        """/albums/{id}/slides LIST (GET) endpoint returns:"""
        album_id = kwargs['id']
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
    @action(detail=True, methods=['post'], url_path='slides')
    def create_slides(self, request, *args, **kwargs):
        """/albums/{id}/slides Reorder Slides, Separate_slides, Reorder
        artworks within slides."""

        album_id = kwargs['id']
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
                _(f'Could not edit slides: {e}'), status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        responses={
            200: PermissionsSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'], url_path='permissions')
    def retrieve_permissions(self, request, *args, **kwargs):
        """Get Permissions /albums/{id}/permissions."""
        album_id = kwargs['id']
        try:
            album = Album.objects.get(pk=album_id)
        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        return Response(
            [
                {
                    'user': {
                        'id': p.user.id,
                        'name': f'{p.user.first_name} {p.user.last_name}',
                    },
                    'permission': [
                        {'id': p.permissions.upper()}  # possible values: view | edit
                    ],
                }
                for p in PermissionsRelation.objects.filter(album__id=album.id)
                if (album.user.username == request.user.username)
                or (
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
                )
            ]
        )

    @extend_schema(
        request=PermissionsSerializer,
        examples=[
            OpenApiExample(
                name='shared_info',
                value=[{'user': 'username', 'permissions': {'id': 'VIEW'}}],
            )
        ],
        responses={
            200: AlbumSerializer,
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['post'], url_path='permissions')
    def create_permissions(self, request, *args, **kwargs):
        """Post Permissions /albums/{id}/permissions."""
        album_id = kwargs['id']
        try:
            album = Album.objects.get(pk=album_id)
            serializer = PermissionsSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            perm = json.loads(request.data.get('permissions'))[0]

            try:
                user = User.objects.get(username=perm.get('user'))
            except User.DoesNotExist:
                return Response(
                    _(f'Invalid user ID: {perm.get("user")}'),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            permissions = perm.get('permissions').get('id')

            if permissions.upper() not in ['VIEW', 'EDIT']:
                return Response(
                    _('Permission invalid. Permission can be either VIEW or EDIT'),
                    status=status.HTTP_404_NOT_FOUND,
                )

            obj, created = PermissionsRelation.objects.update_or_create(
                permissions=permissions.upper(),
                album=album,
                user=user,
            )

            return Response(
                [
                    {
                        'user': {
                            'id': p.user.id,
                            'name': f'{p.user.first_name} {p.user.last_name}',
                        },
                        'permission': [
                            {
                                'id': p.permissions.upper()  # possible values: view | edit
                            }
                        ],
                    }
                    for p in PermissionsRelation.objects.filter(album__id=album.id)
                ]
            )

        except Album.DoesNotExist:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'], url_path='permissions')
    def destroy_permissions(self, request, *args, **kwargs):
        """Delete Permissions /albums/{id}/permissions/ "Unshare" album.

        If the user is the owner of the album, all sharing permissions
        will be deleted. If the user is just a user who this album is
        shared with, only their own sharing permission will be deleted.
        """
        album_id = kwargs['id']
        try:
            album = Album.objects.get(pk=album_id)
            shares_per_album = [
                p.user.username
                for p in PermissionsRelation.objects.filter(album__id=album_id)
            ]

            # If User is owner of Album
            if album.user.username == request.user.username:
                # all shares (permissions) per Album are deleted
                perm_rel = PermissionsRelation.objects.filter(album__id=album_id)
                for p in perm_rel:
                    p.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            # If User shares Album but is not owner
            if request.user.username in shares_per_album:
                # the user's share (permission) is deleted
                PermissionsRelation.objects.filter(user=request.user).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            # User is not owner nor has shares (permissions)
            return Response(status=status.HTTP_403_FORBIDDEN)

        except (Album.DoesNotExist, ValueError):
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

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
    def download(self, request, *args, **kwargs):
        # Todo: now only pptx, later also PDF
        album_id = kwargs['id']
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
        data = {
            'artworks': {
                'artists': 'Artists',
                'credits': 'Credits',
                'date': 'Date of creation',
                'description': 'Description',
                'dimensions': 'Dimensions',
                'keywords': 'Keywords',
                'license': 'License',
                'location_current': 'Current location',
                'location_of_creation': 'Place of creation',
                'material': 'Material/Technique',
                'title': 'Title',
                'title_notes': 'Notes on problematic terms',
            },
        }

        return Response(data)


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
            ret.append(
                {
                    'id': permission_type[0],
                    'label': permission_type[1],
                    'default': settings.PERMISSIONS_DEFAULT.get(permission_type[0]),
                }
            )
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
