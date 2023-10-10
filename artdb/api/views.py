import logging
from rest_framework.exceptions import ParseError
from django.contrib.auth.models import User

import re
from django.contrib.postgres.search import SearchVector

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    OpenApiExample
)
from django.db.models import Q, ExpressionWrapper, BooleanField

from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from artworks.models import (
    Artist,
    Keyword,
    Location,
    Artwork,
    Album,
    AlbumMembership,
    PermissionsRelation

)

from .serializers import (
    ArtworkSerializer,
    AlbumSerializer, SlidesSerializer, UpdateAlbumSerializer, CreateAlbumSerializer, SearchRequestSerializer,
    SearchResponseSerializer, PermissionsSerializer,

)

logger = logging.getLogger(__name__)


def artworks_in_slides(album):
    artworks_in_slides = []

    if album.slides:
        for artworks_list in album.slides:
            for slides in artworks_list:
                artworks = Artwork.objects.filter(
                    id=slides.get('id'))
                for artwork in artworks:
                    if artwork in album.artworks.all():
                        artworks_in_slides.append(
                            {
                                "id": artwork.id,
                                "image_original": artwork.image_original.url if artwork.image_original else None,
                                "credits": artwork.credits,
                                "title": artwork.title,
                                "date": artwork.date,
                                "artists": [
                                    {
                                        "value": artist.name,
                                        "id": artist.id
                                    }
                                    for artist in artwork.artists.all()]
                            }
                        )

    return artworks_in_slides


def simple_album_object(album):
    return Response(
        {
            "id": album.id,
            "title": album.title,
            "number_of_artworks": album.artworks.all().count(),
            "slides": [artwork_in_slide for artwork_in_slide in artworks_in_slides(album)],
            "owner": {
                "id": album.user.id,
                "name": f"{album.user.first_name} {album.user.last_name}"
            },
            "permissions": [
                {
                    "user": {
                        "id": p.user.id,
                        "name": f"{p.user.first_name} {p.user.last_name}"
                    },
                    "permission": [
                        {
                            "id": p.permissions  # possible values: view | edit
                        }
                    ]
                }
                for p in PermissionsRelation.objects.filter(album__id=album.id)]
        }
    )


class ArtworksViewSet(viewsets.GenericViewSet):
    """
    list_artworks:
    GET all artworks.

    retrieve_artwork:
    GET specific artwork.

    retrieve_albums_per_artwork:
    GET albums the current user has added this artwork to.

    search:
    GET artworks according to search parameters.

    list_search_filters:
    GET filters for search.

    """

    serializer_class = ArtworkSerializer
    queryset = Artwork.objects.all()
    parser_classes = (FormParser, MultiPartParser)
    filter_backends = (DjangoFilterBackend,)
    UserModel = get_user_model()

    @extend_schema(
        request=serializer_class,
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                description='',
                default=100
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                required=False,
                description='',
            )
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_artworks(self, request, *args, **kwargs):
        limit = int(request.GET.get('limit')) if request.GET.get('limit') else 100  # default limit
        offset = int(request.GET.get('offset')) if request.GET.get('offset') else None

        results = Artwork.objects.all()

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
                "total": results.count(),
                "results": [
                    {
                        "id": artwork.id,
                        "image_original": artwork.image_original.url if artwork.image_original else None,
                        "credits": artwork.credits,
                        "title": artwork.title,
                        "date": artwork.date,
                        "artists": [
                            {
                                "id": artist.id,
                                "value": artist.name
                            }
                            for artist in artwork.artists.all()
                        ]
                    }
                    for artwork in results]
            }
        )

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_artwork(self, request, item_id=None):
        try:
            artwork = Artwork.objects.get(pk=item_id)
        except Artwork.DoesNotExist:
            return Response(_('Artwork does not exist'), status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": artwork.id,
                "image_original": artwork.image_original.url if artwork.image_original else None,
                "credits": artwork.credits,
                "license": "String",  # placeholder for future field change, see ticket 2070
                "title": artwork.title,
                "title_english": artwork.title_english,
                "title_notes": "String",  # placeholder for future field change, see ticket 2070
                "date": artwork.date,
                "material": artwork.material,
                "dimensions": artwork.dimensions,
                "description": artwork.description,
                "location_of_creation": {
                    "id": artwork.location_of_creation.id,
                    "value": artwork.location_of_creation.name,
                } if artwork.location_of_creation else {},
                "location_current": {
                    "id": artwork.location_current.id,
                    "value": artwork.location_current.name,
                } if artwork.location_current else {},
                "artists": [
                    {
                        "id": artist.id,
                        "value": artist.name
                    }
                    for artist in artwork.artists.all()
                ],
                "keywords": [
                    {
                        "id": keyword.id,
                        "value": keyword.name
                    } for keyword in artwork.keywords.all()
                ]
            }
        )

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_albums_per_artwork(self, request, item_id=None):
        try:
            artwork = Artwork.objects.get(pk=item_id)
            albums = artwork.album_set.all()
        except Artwork.DoesNotExist:
            return Response(_('Artwork does not exist'), status=status.HTTP_404_NOT_FOUND)

        return Response([
            {
                "id": album.id,
                "value": album.title,
            }
            for album in albums]
        )

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_search_filters(self, request, *args, **kwargs):

        data = {
            "title": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "source": {
                            "type": "string"
                        }
                    }
                },
                "title": "title",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/titles/",
                    "placeholder": "enter title",
                    "order": 1
                }
            },
            "artist": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "source": {
                            "type": "string"
                        }
                    }
                },
                "title": "artist",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/artists/",
                    "placeholder": "enter artist",
                    "order": 2
                }
            },
            "place_of_production": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "source": {
                            "type": "string"
                        }
                    }
                },
                "title": "place of production",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/locations/",
                    "placeholder": "enter place of production",
                    "order": 3
                }
            },
            "current_location": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "source": {
                            "type": "string"
                        }
                    }
                },
                "title": "current location",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/locations/",
                    "placeholder": "enter current location",
                    "order": 4
                }
            },
            "keywords": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {
                            "type": "string"
                        },
                        "source": {
                            "type": "string"
                        }
                    }
                },
                "title": "keywords",
                "x-attrs": {
                    "placeholder": "enter keywords",
                    "order": 5,
                    "field_format": "full",
                    "field_type": "chips",
                    "allow_unknown_entries": False,
                    "dynamic_autosuggest": True,
                    "source": "/autosuggest/v1/keywords/"
                }
            },
            "date": {
                "type": "object",
                "properties": {
                    "date_from": {
                        "type": "string"
                    },
                    "date_to": {
                        "type": "string"
                    }
                },
                "title": "date from, to",
                "additionalProperties": False,
                "x-attrs": {
                    "field_format": "full",
                    "field_type": "date",
                    "date_format": "year",
                    "placeholder": {
                        "date": "enter date"
                    },
                    "order": 6
                }
            }
        }

        return Response(data)

    @extend_schema(
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
                        'filters':
                            [
                                {
                                    'id': 'artist',
                                    'filter_values': ['rubens', {'id': 786}],
                                }
                            ],
                    }
                ]
            ),
            OpenApiExample(
                name='search with filter type date',
                value=[
                    {
                        'limit': 0,
                        'offset': 0,
                        'exclude': [123, 345],  # with artwork ids
                        'q': '',  # the string from general search
                        'filters':
                            [
                                {
                                    "id": "date",
                                    "filter_values": {
                                        "date_from": "2000",
                                        "date_to": "2001"
                                    }
                                }
                            ],
                    }
                ]
            )
        ],
        responses={
            200: SearchResponseSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def search(self, request, *args, **kwargs):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        search_req_data = serializer.data.get('search_request')[0]

        limit = search_req_data.get('limit') if search_req_data.get('limit') else None
        offset = search_req_data.get('offset') if search_req_data.get('offset') else None
        filters = search_req_data.get('filters', [])
        searchstr = search_req_data.get('q', '')
        excluded = search_req_data.get('exclude', [])

        results = Artwork.objects.exclude(id__in=[str(i) for i in excluded]) if excluded else Artwork.objects.all()
        q_objects = Q()

        for i in filters:

            if i['id'] == 'title':
                q_objects |= filter_title(i['filter_values'], q_objects, results)

            elif i['id'] == 'artist':
                q_objects |= filter_artist(i['filter_values'], q_objects, results)

            elif i['id'] == 'place_of_production':
                q_objects |= filter_place_of_production(i['filter_values'], q_objects, results)

            elif i['id'] == 'current_location':
                q_objects |= filter_current_location(i['filter_values'], q_objects, results)

            elif i['id'] == 'keywords':
                q_objects |= filter_keywords(i['filter_values'], q_objects, results)

            elif i['id'] == 'date':
                q_objects |= filter_date(i['filter_values'], q_objects, results)

            else:
                raise ParseError('Invalid filter id. Filter id can only be title, artist, place_of_production, '
                                 'current_location, keywords, or date.', 400)

        results = results.filter(q_objects)

        results = results.annotate(search=SearchVector("title", "title_english", "artists", "material",
                                                       "dimensions", "description", "credits", "keywords",
                                                       "location_of_creation", "location_current"),
                                   )#.filter(search__icontains=searchstr).order_by('id').distinct('id')
        # Test: this version does not combine q and a
        print(results)
        search_terms = searchstr.split(' ')
        for term in search_terms:
            if term:
                q_objects |= Q(search__icontains=term)
        print(results.filter(search__icontains=searchstr).order_by('id').distinct('id'))
        results = results.filter(q_objects)
        # test
        print(results)

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        results = results[offset:end]

        return Response(
            {
                "total": results.count(),
                "results": [
                    {
                        "id": artwork.id,
                        "image_original": [artwork.image_original.url if artwork.image_original else None],
                        "credits": artwork.credits,
                        "title": artwork.title,
                        "date": artwork.date,
                        "artists": [
                            {
                                "value": artist.name,
                                "id": artist.id
                            }
                            for artist in artwork.artists.all()]
                    }
                    for artwork in results]
            }
        )


def filter_title(filter_values, q_objects, results):
    """
     Should filter artworks whose title include the string if given, AND the artworks with given id
    """
    for val in filter_values:
        if isinstance(val, str):
            q_objects |= Q(title__icontains=val) | Q(title_english__icontains=val)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(id=val.get('id'))
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return q_objects


def filter_artist(filter_values, q_objects, results):
    """
     Should filter artworks whose artist name includes the string if given, AND the artworks for artist which has
     the given id
    """
    for val in filter_values:
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(artists__id=val.get('id'))

        if isinstance(val, str):
            terms = val.split(" ")
            for term in terms:
                q_objects |= Q(artists__name__unaccent__icontains=term)

    return q_objects


def filter_place_of_production(filter_values, q_objects, results):
    """
     Should filter artworks whose place of production includes the string if given, AND
     the artworks for place of production which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(location_of_creation__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(location_of_creation__id=val.get('id'))
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return q_objects


def filter_current_location(filter_values, q_objects, results):
    """
     Should filter artworks whose current location includes the string if given, AND
     the artworks for current location which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects |= Q(location_current__in=locations)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(location_current__id=val.get('id'))
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return q_objects


def filter_keywords(filter_values, q_objects, results):
    """
     Should filter artworks whose keywords include the string if given, AND
     the artworks for keyword which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            keywords = Keyword.objects.filter(name__icontains=val)
            q_objects |= Q(keywords__in=keywords)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects |= Q(keywords__id=val.get('id'))
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

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
        return Response(_('Invalid filter_value format. See example below for more information.'))

    return q_objects


class AlbumViewSet(viewsets.ViewSet):
    """
    list_folders:
    List of all the users albums /folders (in anticipation that there will be folders later)

    list_albums:
    GET all the users albums.

    retrieve_album:
    GET specific album.

    retrieve_slides_per_album:
    GET /albums/{id}/slides LIST (GET) endpoint

    retrieve_permissions_per_album:
    GET /albums/{id}/permissions

    create_album:
    POST new album with given title.

    edit_slides:
    POST /albums/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

    append_artwork
    POST /albums/{id}/append_artwork
    Append artwork to slides as singular slide [{'id': x}]

    create_permissions
    POST /albums/{id}/permissions

    create_folder:
    POST

    update_album:
    PATCH specific album and album’s fields

    delete_album:
    DELETE specific album



    """

    queryset = Album.objects.all()
    parser_classes = (FormParser, MultiPartParser)
    filter_backends = (DjangoFilterBackend,)
    UserModel = get_user_model()

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
            )
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_folders(self, request, *args, **kwargs):
        '''
        List of all the users albums /folders (in anticipation that there will be folders later)
        '''

        limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
        offset = int(request.GET.get('offset')) if request.GET.get('offset') else None

        # TODO: to complete when folders are relevant

        dummy_data = [{
            'title': 'Some title',
            'ID': 1111,
            'shared_info': 'Some shared info',
            '# of works': 89,
            'thumbnail': 'https://www.thumbnail.com'
        },
            {
                'title': 'Some title2',
                'ID': 2222,
                'shared_info': 'Some shared info2',
                '# of works': 56,
                'thumbnail': 'https://www.thumbnail.com'
            }
        ]
        # TODO
        serializer = AlbumSerializer(self.queryset, many=True)

        limit = limit if limit != 0 else None

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        results = dummy_data[offset:end]

        return Response(results)

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
            )
        ],
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_albums(self, request, *args, **kwargs):
        '''
        List of all Albums (used for getting latest Albums) /albums
        '''
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
                "total": len(results),
                "results": [
                    {
                        "id": album.id,
                        "title": album.title,
                        "number_of_artworks": album.artworks.all().count(),  # number of artworks in a specific album
                        "artworks": [
                                        # the first 4 artworks from all slides: [[{"id":1}], [2,3], [4,5]] -> 1,2,3,4,max 4 objects
                                        {
                                            "id": artwork_id,
                                            "image_original": Artwork.objects.get(
                                                id=artwork_id).image_original.url if Artwork.objects.get(
                                                id=artwork_id).image_original else None,
                                            "title": Artwork.objects.get(id=artwork_id).title
                                        }

                                       for artwork_id in slides_ids if artwork_id

                                    ][:4] if album.slides else [],
                        "owner": {
                            "id": album.user.id,
                            "name": f"{album.user.first_name} {album.user.last_name}"
                        },
                        "permissions": [
                            {
                                "user": {
                                    "id": p.user.id,
                                    "name": f"{p.user.first_name} {p.user.last_name}"
                                },
                                "permission": [
                                    {
                                        "id": p.permissions  # possible values: view | edit
                                    }
                                ]
                            }
                            for p in PermissionsRelation.objects.filter(album__id=album.id)]

                    }
                    for album in results]
            }
        )

    @extend_schema(
        request=AlbumSerializer,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_album(self, request, album_id=None):  # TODO update
        '''
        List of Works (Slides) in a specific Album /albums/{id}
        '''

        # todo

        # - Download album with slides  - usually needs to take more detailed settings like language,
        # which entry details to include) /album/{id}/download ? definite in version version: language,
        # file type + image metadata (title, artist - current status)
        try:
            album = Album.objects.get(pk=album_id)
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        # TODO slides ticket
        # todo: artworks from slides or all artworks regardless?
        # todo: check if it belongs to album? could be a solution for now. Otherwise first decide whether to influence artworks/album with slides

        return simple_album_object(album)

    @extend_schema(
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_slides_per_album(self, request, album_id=None):
        '''
        /albums/{id}/slides LIST (GET) endpoint returns:
        '''

        try:
            album = Album.objects.get(pk=album_id)
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        # todo: slides tickets

        return Response(
            [
                artworks_in_slides(album)
            ]
        )

    @extend_schema(
        methods=['POST'],
        request=CreateAlbumSerializer,  # todo fix serializers
        responses={
            200: AlbumSerializer
        }
    )
    def create_album(self, request, *args, **kwargs):
        '''
        Create Album /albums/{id}
        '''
        try:
            title = request.data.get('title')
            album = Album.objects.create(title=title, user=request.user)
            album.save()

            return simple_album_object(album)
        except ValueError:
            return Response(
                _('Album user must be a user instance'), status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        methods=['POST'],
        request=SlidesSerializer,
        examples=[
            OpenApiExample(
                name='slides',
                value=[[{'id': 123}, {'id': 456}], [{'id': 789}], [{'id': 123}]],
            )],
        responses={
            200: AlbumSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'), }
    )
    def edit_slides(self, request, album_id=None, slides=None, *args, **kwargs):
        '''
        /albums/{id}/slides
        Reorder Slides,
        Separate_slides,
        Reorder artworks within slides
        '''

        try:
            album = Album.objects.get(pk=album_id)
            slides_serializer = SlidesSerializer(data=request.data)

            # Validate slides object
            if not slides_serializer.is_valid():
                return Response(
                    _('Slides format incorrect'), status=status.HTTP_400_BAD_REQUEST
                )

            slides = slides_serializer.data.get('slides')

            # Validate artworks within slides & assign artwork to album if missing and artwork exists
            artworks_to_remove = []
            artworks = []
            for artworks_list in slides:
                for slide in artworks_list:
                    try:
                        artworks.append(Artwork.objects.get(
                            id=slide.get('id')))
                    except Artwork.DoesNotExist:
                        artworks_to_remove.append(slide.get('id'))

                    for artwork in artworks:
                        if artwork not in album.artworks.all():
                            # album.artworks.add(artwork)  # used to be

                            # Temporary solution to avoid IntegrityError
                            AlbumMembership.objects.get_or_create(collection=album, artwork=artwork)

            # Update slides object after removing non existing artwork
            slides = [l for l in slides for d in l if d.get('id') not in artworks_to_remove]
            print(slides)
            album.slides = slides
            album.save()
            return Response(album.slides)

        except TypeError as e:
            return Response(
                _(f'Could not edit slides: {e}'), status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        methods=['POST'],
        parameters=[
            OpenApiParameter(
                name='artwork_id',
                type=OpenApiTypes.INT,
                required=True,
                description='',
                default=0
            )],
        responses={
            200: AlbumSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'), }
    )
    def append_artwork(self, request, album_id=None, artwork_id=None, *args, **kwargs):
        '''
        /albums/{id}/append_artwork
        Append artwork to slides as singular slide [{'id': x}]
        '''

        # Todo: Decide whether we need to check if an artwork object ({'id': x}) is already present within the slides.
        #   For now, an artwork is appended as slide regardless

        try:
            album = Album.objects.get(pk=album_id)
            if not album.slides:
                album.slides = []

            # Check if artwork exists
            artwork = Artwork.objects.get(pk=int(request.GET.get('artwork_id')))
            # Assign artwork to album
            # album.artworks.add(artwork)  # used to be

            # Temporary solution to avoid IntegrityError
            AlbumMembership.objects.get_or_create(collection=album, artwork=artwork)

            album.slides.append([{'id': artwork.id}])
            album.save()
            return Response([
                {
                    "id": album.id,
                    "title": album.title,
                    "slides": album.slides,
                }
            ])

        except Artwork.DoesNotExist:
            return Response(
                _('There is no artwork associated with the given id.'), status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        methods=['GET'],
        responses={
            200: PermissionsSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        }
    )
    def retrieve_permissions_per_album(self, request, album_id=None):
        '''
        Get Permissions /albums/{id}/permissions
        '''

        try:
            album = Album.objects.get(pk=album_id)
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        return Response(
            [
                {
                    "user": {
                        "id": p.user.id,
                        "name": f"{p.user.first_name} {p.user.last_name}"
                    },
                    "permission": [
                        {
                            "id": p.permissions.upper()  # possible values: view | edit
                        }
                    ]
                }
                for p in
                PermissionsRelation.objects.filter(album__id=album.id)]
        )

    @extend_schema(
        methods=['POST'],
        request=PermissionsSerializer,
        examples=[
            OpenApiExample(
                name='shared_info',
                value=[
                    {
                        "user_id": 123,
                        "permissions": {
                            "id": "VIEW"
                        }
                    }
                ]
            )],
        responses={
            200: AlbumSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        }
    )
    def create_permissions(self, request, partial=True, album_id=None, *args, **kwargs):
        '''
        Post Permissions /albums/{id}/permissions
        '''

        try:
            album = Album.objects.get(pk=album_id)
            serializer = PermissionsSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            for perm in dict(serializer.validated_data).get('permissions'):

                try:
                    user = User.objects.get(pk=perm.get('user_id'))
                except User.DoesNotExist:
                    return Response(_(f'Invalid user ID: {perm.get("user_id")}'), status=status.HTTP_400_BAD_REQUEST)

                permissions = perm.get('permissions').get('id')

                if permissions.upper() not in ['VIEW', 'EDIT']:
                    return Response(_('Permission invalid. Permission can be either VIEW or EDIT'),
                                    status=status.HTTP_404_NOT_FOUND)

                obj, created = PermissionsRelation.objects.update_or_create(
                    permissions=permissions.upper(),
                    album=album,
                    user=user
                )

            return Response(
                [
                    {
                        "user": {
                            "id": p.user.id,
                            "name": f"{p.user.first_name} {p.user.last_name}"
                        },
                        "permission": [
                            {
                                "id": p.permissions.upper()  # possible values: view | edit
                            }
                        ]
                    }
                    for p in
                    PermissionsRelation.objects.filter(album__id=album.id)]
            )

        except Album.DoesNotExist:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

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
                        value=[{
                            'title': 'Some title',
                            'ID': 1111,
                            'shared_info': 'Some shared info',
                            '# of works': 89,
                            'thumbnail': 'https://www.thumbnail.com'
                        }],
                    )],
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT
        }
    )
    def create_folder(self, request, *args, **kwargs):
        '''
        Create Folder /albums/{id}
        '''
        # todo
        # Create folder with given data
        # validate object
        dummy_data = {
            'title': request.data.get('title'),
            'ID': 1111,
            'shared_info': 'Some shared info',
            '# of works': 89,
            'thumbnail': 'https://www.thumbnail.com'
        }
        # Todo: update response
        return Response(dummy_data)

    @extend_schema(
        methods=['PATCH'],
        request=UpdateAlbumSerializer,
        responses={
            200: AlbumSerializer,
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        }
    )
    def update_album(self, request, partial=True, album_id=None, *args, **kwargs):
        '''
        Update Album /albums/{id}
        '''

        try:
            album = Album.objects.get(pk=album_id)
            album.title = request.data.get('title')

            serializer = UpdateAlbumSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            album.save()
            return simple_album_object(album)

        except Album.DoesNotExist:
            return Response(_('Album does not exist '), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        methods=['DELETE'],
    )
    def delete_album(self, request, album_id=None, *args, **kwargs):
        '''
        Delete Album /albums/{id}
        '''
        try:
            album = Album.objects.get(pk=album_id)
            album.delete()
            return Response(_(f'Album {album.title} was deleted'), status=status.HTTP_200_OK)
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.GenericViewSet):

    @extend_schema(
        tags=['user'],
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            data = {
                'uuid': request.user.username,
                'name': request.user.get_full_name(),
                'email': request.user.email,
            }
            return Response(data)
        except AttributeError:
            return Response(
                _('Authentication credentials were not provided.'), status=status.HTTP_403_FORBIDDEN
            )
