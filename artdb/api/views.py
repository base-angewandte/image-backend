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
                        'exclude': ['id123', 'id345'],  # with artwork ids
                        'q': 'searchstring',  # the string from general search
                        'filters':
                            [
                                {
                                    'id': 'artist',
                                    'filter_values': ['rubens', {'id': 'id786'}],
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
                        'exclude': ['id123', 'id345'],  # with artwork ids
                        'q': 'searchstring',  # the string from general search
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
        filters = search_req_data.get('filters')
        filter_values = filters[0].get('filter_values')
        searchstr = search_req_data.get('q')
        excluded = search_req_data.get('exclude')

        results = Artwork.objects.exclude(id__in=[str(i) for i in excluded])
        q_objects = Q()

        for i in filters:
            if i['id'] == 'title':
                results = filter_title(filter_values, q_objects, results)

            elif i['id'] == 'artist':
                results = filter_artist(filter_values, q_objects, results)

            elif i['id'] == 'place_of_production':
                results = filter_place_of_production(filter_values, q_objects, results)

            elif i['id'] == 'current_location':
                results = filter_current_location(filter_values, q_objects, results)

            elif i['id'] == 'keywords':
                results = filter_keywords(filter_values, q_objects, results)

            elif i['id'] == 'date':
                results = filter_date(filter_values, q_objects, results)

            else:
                raise ParseError('Invalid filter id. Filter id can only be title, artist, place_of_production, '
                                 'current_location, keywords, or date.', 400)

        results = results.annotate(search=SearchVector("title", "title_english", "artists", "material",
                                             "dimensions", "description", "credits", "keywords",
                                             "location_of_creation", "location_current"),
                         ).filter(search__icontains=searchstr).distinct()

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
                    [
                        {
                            "title": artwork.title,
                            "artist": [artist.name for artist in artwork.artists.all()],
                            "date": artwork.date,
                            "image_urls":
                            # todo list of strings, retriever urls. Is this what is needed ?
                                [artwork.image_original if artwork.image_original else None],
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


def filter_title(filter_values, q_objects, results):
    """
     Should filter artworks whose title include the string if given, AND the artworks with given id
    """
    for val in filter_values:
        if isinstance(val, str):
            q_objects.add(Q(title__icontains=val) | Q(title_english__icontains=val), Q.AND)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(id=val.get('id')), Q.AND)
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return results.filter(q_objects)


def filter_artist(filter_values, q_objects, results):
    """
     Should filter artworks whose artist name includes the string if given, AND the artworks for artist which has
     the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            terms = [term.strip() for term in val.split()]
            for term in terms:
                q_objects.add(
                    (Q(artists__name__unaccent__icontains=term) | Q(artists__synonyms__unaccent__icontains=term)),
                    Q.AND,
                )
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(artists__id=val.get('id')), Q.AND)
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return results.filter(q_objects)


def filter_place_of_production(filter_values, q_objects, results):
    """
     Should filter artworks whose place of production includes the string if given, AND
     the artworks for place of production which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects.add(Q(location_of_creation__in=locations), Q.AND)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(location_of_creation__id=val.get('id')), Q.AND)
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return results.filter(q_objects)


def filter_current_location(filter_values, q_objects, results):
    """
     Should filter artworks whose current location includes the string if given, AND
     the artworks for current location which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            locations = Location.objects.filter(name__icontains=val)
            q_objects.add(Q(location_current__in=locations), Q.AND)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(location_current__id=val.get('id')), Q.AND)
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return results.filter(q_objects)


def filter_keywords(filter_values, q_objects, results):
    """
     Should filter artworks whose keywords include the string if given, AND
     the artworks for keyword which has the given id
    """
    for val in filter_values:
        if isinstance(val, str):
            keywords = Keyword.objects.filter(name__icontains=val)
            q_objects.add(Q(keywords__in=keywords), Q.AND)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects.add(Q(keywords__id=val.get('id')), Q.AND)
        else:
            raise ParseError('Invalid filter_value format. See example below for more information.', 400)

    return results.filter(q_objects)


def filter_date(filter_values, q_objects, results):

    if isinstance(filter_values, dict):

        if re.match(r'^[12][0-9]{3}$', filter_values.get('date_from')):
            q_objects.add(Q(date_year_from__gte=filter_values['date_from']), Q.AND)
        elif re.match(r'^[12][0-9]{3}$', filter_values.get('date_to')):
            q_objects.add(Q(date_year_to__lte=filter_values['date_to']), Q.AND)
        else:
            raise ParseError(
                'Only dates of format YYYY can be used as date filter values',
                400,
            )

    else:
        return Response(_('Invalid filter_value format. See example below for more information.'))

    return results.filter(q_objects)


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

        # todo

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

        return Response({
            "permissions": [{"user_id": i.user.id, "permissions": {"id": i.permissions.upper()}} for i in
                            PermissionsRelation.objects.filter(album__id=album.id)]

        })

    @extend_schema(
        methods=['POST'],
        request=PermissionsSerializer,
        examples=[
            OpenApiExample(
                name='shared_info',
                value=[
                    {
                        "user_id": "123xd3",
                        "permissions": {
                            "id": "view"
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

                user = User.objects.get(pk=perm.get('user_id'))
                permissions = perm.get('permissions').get('id')

                obj, created = PermissionsRelation.objects.update_or_create(
                    permissions=permissions,
                    album=album,
                    user=user
                )

            return Response(serializer.data)

        except Album.DoesNotExist:
            return Response(_('Album does not exist '), status=status.HTTP_404_NOT_FOUND)

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

            album_serializer = AlbumSerializer(album)
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
