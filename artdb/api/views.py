import logging

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
    ArtworkCollection,
    ArtworkCollectionMembership,

)

from .serializers import (
    ArtworkSerializer,
    AlbumSerializer,

)

logger = logging.getLogger(__name__)


class ArtworksViewSet(viewsets.GenericViewSet):
    """
    list:
    GET all artworks.

    retrieve:
    GET specific artwork.

    """

    serializer_class = ArtworkSerializer
    queryset = Artwork.objects.all()
    parser_classes = (FormParser, MultiPartParser)
    filter_backends = (DjangoFilterBackend,)
    UserModel = get_user_model()

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = ArtworkSerializer(self.queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve(self, request, item_id=None):
        try:
            artwork = Artwork.objects.get(pk=item_id)
        except Artwork.DoesNotExist:
            return Response(_('Artwork does not exist'), status=status.HTTP_404_NOT_FOUND)

        serializer = ArtworkSerializer(artwork)
        return Response(serializer.data)

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
            OpenApiParameter(
                name='title',
                type=OpenApiTypes.STR,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='artist',
                type=OpenApiTypes.STR,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='keyword',
                type=OpenApiTypes.STR,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='date_year_from',
                type=OpenApiTypes.DATETIME,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='date_year_to',
                type=OpenApiTypes.DATETIME,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='origin',
                type=OpenApiTypes.STR,
                required=False,
                description='',
            ),
            OpenApiParameter(
                name='location',
                type=OpenApiTypes.STR,
                required=False,
                description='',
            ),
        ],
        methods=['GET'],
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def search_artworks(self, request, item_id=None):
        # TODO:
        # Default (latest?) artworks on initial page load (could this be part of search?) - LIST /albums
        # include pagination
        # also exclude param with list with ids of artworks
        # start with GET - if we run into limits --> might need to add /search  POST after all

        limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
        offset = int(request.GET.get('offset')) if request.GET.get('offset') else None

        results = Artwork.objects.all()
        artwork_title = request.GET.get('title')
        artist_name = request.GET.get('artist')
        keyword = request.GET.get('keyword')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        location_of_creation = request.GET.get('origin')  # origin
        location_current = request.GET.get('location')  # location
        q_objects = Q()

        if location_of_creation:
            locations = Location.objects.filter(name__istartswith=location_of_creation)
            q_objects.add(Q(location_of_creation__in=locations), Q.AND)
        if location_current:
            locations = Location.objects.filter(name__istartswith=location_current)
            q_objects.add(Q(location_current__in=locations), Q.AND)
        if artist_name:
            terms = [term.strip() for term in artist_name.split()]
            for term in terms:
                q_objects.add(
                    (Q(artists__name__unaccent__icontains=term) | Q(artists__synonyms__unaccent__icontains=term)),
                    Q.AND,
                )
        if keyword:
            keywords = Keyword.objects.filter(name__icontains=keyword)
            q_objects.add(Q(keywords__in=keywords), Q.AND)
        if date_from:
            try:
                year = int(date_from)
                q_objects.add(Q(date_year_from__gte=year), Q.AND)
            except ValueError as err:
                logger.error(err)
                return []
        if date_to:
            try:
                year = int(date_to)
                q_objects.add(Q(date_year_to__lte=year), Q.AND)
            except ValueError as err:
                logger.error(err)
                return []
        if artwork_title:
            q_objects.add(Q(title__icontains=artwork_title) |
                          Q(title_english__icontains=artwork_title), Q.AND)

        results = results.distinct().filter(q_objects)

        end = offset + limit if offset and limit else None
        results = results[offset:end]

        serializer = ArtworkSerializer(results, many=True)

        return Response({
            'total_results': results.count(),
            'data': serializer.data
        })


class AlbumViewSet(viewsets.ViewSet):
    """
    list_folders:
    List of all the users albums /folders (in anticipation that there will be folders later)

    list_albums:
    GET all the users albums. #todo define

    retrieve_album:
    GET /albums/{id}

    retrieve_slides_per_album:
    GET /albums/{id}/slides LIST (GET) endpoint   # todo??

    edit_slides:
    POST /albums/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

    create_folder:
    POST

    update_album:
    PATCH

    delete_album:
    DELETE



    """

    serializer_class = AlbumSerializer
    queryset = ArtworkCollection.objects.all()
    parser_classes = (FormParser, MultiPartParser)
    filter_backends = (DjangoFilterBackend,)
    UserModel = get_user_model()

    @extend_schema(
        request=serializer_class,
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
        dummy_data = [{
            'title': 'Some title',
            'ID': 1111,
            'shared_info': 'Some shared info',
            '# of works': 89,
            'thumbnail': 'https://www.thumbnail.com'
        }]
        # WIP todo
        # also todo  LIMIT & SORTING PARAMS
        serializer = AlbumSerializer(self.queryset, many=True)
        return Response(dummy_data)

    @extend_schema(
        request=serializer_class,
        parameters=[OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            required=False,
            description='',
        )],
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
        serializer = AlbumSerializer(self.queryset, many=True)
        data = serializer.data[0:limit]
        return Response(data)

    @extend_schema(
        request=serializer_class,
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
            album = ArtworkCollection.objects.get(pk=album_id)
        except ArtworkCollection.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

        serializer = AlbumSerializer(album)
        return Response(serializer.data)

    @extend_schema(
        request=serializer_class,
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
        # TODO note: works but with dummy data
        dummy_data = [{
            'title': 'Some slides title 1',
            'artist': 'Joe Jonas',
            'image': 'https://www.thumbnail.com/imageid234',
            'quick_info': 'Some quick info',
            # query flag nested info?
        },
            {
                'title': 'Some slides title 2',
                'artist': 'Joe Jonas',
                'image': 'https://www.thumbnail.com/imageid234',
                'quick_info': 'Some quick info',
                # query flag nested info?
            }
        ]
        # todo 2 update serializer once the model is set
        serializer = ArtworkSerializer(self.queryset, many=True)
        return Response(dummy_data)

    @extend_schema(
        methods=['POST'],
        parameters=[
            OpenApiParameter(
                name='id list',
                type=OpenApiTypes.OBJECT,
                required=False,
                description='Desired order or arrangement of slides within album, and/or albums within slides',
            ),
        ],
        examples=[
            OpenApiExample(
                name='id list',
                value=[[{'id': 'abc1'}, {'id': 'xyz2'}], [{'id': 'fgh23'}], [{'id': 'jk54'}]]
            )],
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )

    def edit_slides(self, request, *args, **kwargs):
        '''
        /albums/{id}/slides
        Reorder Slides
        Separate_slides
        Reorder artworks within slides
        '''

        try:
            # Pass an object with a new order or arrangement
            # order by pk given

            dummy_data = [{
                'title': 'Some slides title 1',
                'artist': 'Joe Jonas',
                'image': 'https://www.thumbnail.com/imageid234',
                'quick_info': 'Some quick info',
                # query flag nested info?
            },
                {
                    'title': 'Some slides title 2',
                    'artist': 'Joe Ponas',
                    'image': 'https://www.thumbnail.com/imageid234',
                    'quick_info': 'Some quick info',
                    # query flag nested info?
                }]

            # data = {key: i for i, key in enumerate(artworks_id_order)}

            return Response(_('OK'), status=status.HTTP_200_OK)
        except:
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
            ),
        ],
        examples=[
            OpenApiExample(
                name='create_folder',
                value=[{
                    'title': 'Some title',
                    'ID': 1111,
                    'shared_info': 'Some shared info',
                    '# of works': 89,
                    'thumbnail': 'https://www.thumbnail.com'
                }
                ],
            )],
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
        return Response(
            _('User preferences do not exist'), status=status.HTTP_404_NOT_FOUND
        )


    def update_album(self, request, partial=True, album_id=None, *args, **kwargs):
        # todo take a look at UserPreferencesDataSerializer if nothing else works
        '''
        Update Album /albums/{id}
        '''
        # todo Alter Shared Info
        #   Rename Album / albums (done)
        #   Alter Shared info
        #       part of album model as a many to many relationship with an additional property for the type of right
        #       (read or write; could be extended later).
        #   in the API response then there is also just a list for the permissions
        #   with dicts/objects containing the user id, name and the type of right (read or write)

        try:
            album = ArtworkCollection.objects.get(pk=album_id)
            album.title = request.data.get('album_title')
            album.save()
            serializer = AlbumSerializer(album)
            return Response(serializer.data)

        except ArtworkCollection.DoesNotExist:
            return Response(_('Album does not exist '), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        methods=['DELETE'],
    )
    def delete_album(self, request, album_id=None, *args, **kwargs):
        '''
        Delete Album /albums/{id}
        '''
        try:
            album = ArtworkCollection.objects.get(pk=album_id)
            album.delete()
        except ArtworkCollection.DoesNotExist or ValueError:
            return Response(_('Album does not exist'), status=status.HTTP_404_NOT_FOUND)

    # todo from Shared INFO / album
    # part of album model as a many


class UserViewSet(viewsets.GenericViewSet):
    # todo update. and user for artworks, etc
    # serializer_class = UserSerializer

    @extend_schema(
        tags=['user'],
    )
    def retrieve(self, request, *args, **kwargs):
        return Response({
            'id': 'username1',
            "first_name": "Hellor",
            "last_name": "World",
            'email': 'u@u.com',
            "is_staff": False,
            "is_active": True,
        })

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
