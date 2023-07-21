import logging
from django.core.exceptions import ValidationError
import jsonschema
from artworks.models import User
# todo remove, for testing purposes
# album = Album.objects.create(title=title, user=test_user)
# test_user = User.objects.last()
from rest_framework.exceptions import ParseError

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

)

from .serializers import (
    ArtworkSerializer,
    AlbumSerializer, SlidesSerializer, UpdateAlbumSerializer, CreateAlbumSerializer, SearchRequestSerializer,
    SearchResponseSerializer,

)

logger = logging.getLogger(__name__)


class ArtworksViewSet(viewsets.GenericViewSet):
    """
    list:
    GET all artworks.

    retrieve:
    GET specific artwork.

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
        limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
        offset = int(request.GET.get('offset')) if request.GET.get('offset') else None

        serializer = ArtworkSerializer(self.queryset, many=True)
        results = serializer.data

        limit = limit if limit != 0 else None

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        results = results[offset:end]

        return Response(results)

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

        serializer = ArtworkSerializer(artwork)
        return Response(serializer.data)

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_search_filters(self, request, *args, **kwargs):
        # todo: has to be dynamic
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
                "title": "Titel",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/titles/",
                    "placeholder": "Titel eintragen",
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
                "title": "Künstler*in",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/artists/",
                    "placeholder": "Künstler*in eintragen",
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
                "title": "Entstehungsort",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/locations/",
                    "placeholder": "Entstehungsort eintragen",
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
                "title": "Standort",
                "x-attrs": {
                    "field_format": "half",
                    "field_type": "chips",
                    "dynamic_autosuggest": True,
                    "allow_unknown_entries": True,
                    "source": "/autosuggest/v1/locations/",
                    "placeholder": "Standort eintragen",
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
                "title": "Schlagwort",
                "x-attrs": {
                    "placeholder": "Schlagwort eintragen",
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
                "title": "Datierung von, bis",
                "additionalProperties": False,
                "pattern": "^\\d{4}(-(0[1-9]|1[0-2]))?(-(0[1-9]|[12]\\d|3[01]))?$",
                "x-attrs": {
                    "field_format": "full",
                    "field_type": "date",
                    "date_format": "day",
                    "placeholder": {
                        "date": "Datum eintragen"
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
                name='search_data',
                value=[
                    {
                        'limit': 0,
                        'offset': 0,
                        'exclude': ['id123', 'id345'],  # with artwork ids
                        'q': 'searchstring',  # the string from general search
                        'filters':
                            [
                                {
                                    'id': 'artist',
                                    'filter_values': ['rubens', {'id': 'id786'}],
                                    # format depending on type of filter, see filter list endpoint
                                }
                            ],
                    }
                ]
            ),
            OpenApiExample(
                name='search_data_date',
                value=[
                    {
                        'limit': 0,
                        'offset': 0,
                        'exclude': ['id123', 'id345'],  # with artwork ids
                        'q': 'searchstring',  # the string from general search
                        'filters':
                            [
                                {
                                    "id": "string",
                                    "filter_values": [{
                                        "date_from": "2000",
                                        "date_to": "2001"
                                    }]
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
        filters = search_req_data.get('filters')
        filter_values = filters[0].get('filter_values')  # todo adapt
        searchstr = search_req_data.get('q')
        excluded = search_req_data.get('exclude')

        results = Artwork.objects.exclude(id__in=[str(i) for i in excluded])
        q_objects = Q()

        # todo test all filters
        # todo: django.core.exceptions.FieldError:
        #   Cannot resolve keyword 'date_from' into field. Choices are: album, albummembership,
        #   artists, checked, created_at, credits, date, date_year_from, date_year_to,

        for i in filters:
            if i['id'] == 'title':
                q_objects = filter_title(filter_values, q_objects)

            if i['id'] == 'artist':
                q_objects = filter_artist(filter_values, q_objects, results)

            if i['id'] == 'place_of_production':
                q_objects = filter_place_of_production(filter_values, q_objects)

            if i['id'] == 'current_location':
                q_objects = filter_current_location(filter_values, q_objects)

            if i['id'] == 'keywords':
                q_objects = filter_keywords(filter_values, q_objects)

            if i['id'] == 'date':
                q_objects = filter_date(filter_values, q_objects)

        # todo validate

        # todo search vector not working as it should

        results = results.annotate(search=SearchVector("title", "title_english", "artists", "material",
                                             "dimensions", "description", "credits", "keywords",
                                             "location_of_creation", "location_current"),
                         ).filter(search=searchstr).distinct()


        results = results.distinct()

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
                "results":
                # version 2: artworks by 'rubens' (or '') Rubenski in the artists field AND the string 'ar' in any data field (except artworks with id excluded ids)
                # data field: postgres fulltext search

                # first filter , then searchstr
                    [
                        {
                            "title": artwork.title,
                            "artist": [artist.name for artist in artwork.artists.all()],
                            "date": artwork.date,
                            "image_urls":
                                [artwork.image_original],  # todo list of strings, retriever urls
                            "albums":
                                [
                                    {
                                        "label": album.title,
                                        "id": album.id
                                    }
                                    for album in artwork.album_set.all()
                                ]
                        }
                        for artwork in results]
            }
        )


def filter_title(filter_values, q_objects):
    for val in filter_values:
        if isinstance(val, str):
            q_objects.add(Q(title__icontains=val) | Q(title_english__icontains=val), Q.AND)
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            return Response(_('Invalid filter_value format. See example below for more information.'))

    return q_objects


def filter_artist(filter_values, q_objects, results):
    for val in filter_values:
        if isinstance(val, str):
            terms = [term.strip() for term in val.split()]
            for term in terms:
                q_objects.add(
                    (Q(artists__name__unaccent__icontains=term) | Q(artists__synonyms__unaccent__icontains=term)),
                    Q.AND,
                )
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            return Response(_('Invalid filter_value format. See example below for more information.'))

    return results.filter(q_objects)


def filter_place_of_production(filter_values, q_objects):
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)  # todo: istartswith or icontains?
            q_objects.add(Q(location_of_creation__in=locations), Q.AND)
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            return Response(_('Invalid filter_value format. See example below for more information.'))

    return q_objects


def filter_current_location(filter_values, q_objects):
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)  # todo: istartswith or icontains?
            q_objects.add(Q(location_current__in=locations), Q.AND)
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            return Response(_('Invalid filter_value format. See example below for more information.'))

    return q_objects


def filter_keywords(filter_values, q_objects):
    for val in filter_values:
        if isinstance(val, str):
            keywords = Keyword.objects.filter(name__icontains=val)
            q_objects.add(Q(keywords__in=keywords), Q.AND)
        if isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            return Response(_('Invalid filter_value format. See example below for more information.'))

    return q_objects


def filter_date(filter_values, q_objects):
    ### todo ask FE:
    # 1. does this pattern fit? "pattern":"^\\d{4}(-(0[1-9]|1[0-2]))?(-(0[1-9]|[12]\\d|3[01]))?$",
    # 2. django.core.exceptions.FieldError:
    #         #   Cannot resolve keyword 'date_from' into field. Choices are: album, albummembership, artists, checked, created_at, credits, date, date_year_from, date_year_to,

    for val in filter_values:
        if isinstance(val, dict):
            for date in val.values():
                if not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', date):
                    raise ParseError(
                        'Only dates of format YYYY-MM-DD can be used as date filter values',
                        400,
                    )
            q_objects.add(Q(date_from__gte=val['date_from']) | Q(date_to__gte=val['date_to']), Q.AND)


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

    create_album:
    POST new album with given title.

    edit_slides:
    POST /albums/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

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

        serializer = AlbumSerializer(self.queryset, many=True)
        results = serializer.data

        limit = limit if limit != 0 else None

        if offset and limit:
            end = offset + limit

        elif limit and not offset:
            end = limit

        else:
            end = None

        results = results[offset:end]

        return Response(results)

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

        # todo 3

        # - Download album with slides  - usually needs to take more detailed settings like language,
        # which entry details to include) /album/{id}/download ? definite in version version: language,
        # file type + image metadata (title, artist - current status)
        try:
            album = Album.objects.get(pk=album_id)
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        serializer = AlbumSerializer(album)
        return Response(serializer.data)

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

        serializer = AlbumSerializer(album)
        results = serializer.data
        return Response(results.get('slides'))

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

        title = request.data.get('title')
        album = Album.objects.create(title=title, user=request.user)
        album.save()
        serializer = AlbumSerializer(album)
        return Response(serializer.data)

    @extend_schema(
        methods=['POST'],
        request=SlidesSerializer,
        examples=[
            OpenApiExample(
                name='slides',
                value=[[{'id': 'abc1'}, {'id': 'xyz2'}], [{'id': 'fgh23'}], [{'id': 'jk54'}]],
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

            if not slides_serializer.is_valid():
                return Response(_('Slides format incorrect'), status=status.HTTP_404_NOT_FOUND)

            serializer = AlbumSerializer(album)
            album.slides = slides_serializer.data.get('slides')
            album.save()
            return Response(serializer.data)

        except TypeError:
            return Response(
                _('Could not edit slides'), status=status.HTTP_404_NOT_FOUND
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
        return Response(dummy_data)

    @extend_schema(
        methods=['PATCH'],
        request=UpdateAlbumSerializer,
        examples=[
            OpenApiExample(
                name='shared_info',
                value=[
                    {
                        'owner': {
                            'id': '123abc',
                            'name': 'Name Surname',
                        },
                        'shared_with': [
                            {
                                'id': '123xd3',
                                'name': 'Name Surname',
                                'permission': {
                                    'id': 'read',  # todo still confusion about this
                                    'label': 'Read',  # # todo if it comes from the vocabulary, BE, else FE)
                                },
                            },
                        ],
                    }
                ]
            )],
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
        # TODO Alter Shared info

        try:
            album = Album.objects.get(pk=album_id)
            album.title = request.data.get('title')

            serializer = UpdateAlbumSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(_('Format incorrect'), status=status.HTTP_404_NOT_FOUND)

            album_serializer = AlbumSerializer(album)
            # Todo : adjust shared info
            shared_info = serializer.validated_data.get('shared_info')
            album.save()
            return Response(album_serializer.data)

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
            return Response(_(f'Album {album.title} was deleted'))
        except Album.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.GenericViewSet):
    # TODO update. and user for artworks, etc

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
                _('User does not exist or is not logged in.'), status=status.HTTP_404_NOT_FOUND
            )
