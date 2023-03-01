import json
from json import JSONDecodeError
from django.contrib.auth.models import User

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
OpenApiExample
)
import json
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status, viewsets
# from rest_framework.exceptions import PermissionDenied
# from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
# from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# from rest_framework_api_key.models import APIKey
# from rest_framework_api_key.permissions import HasAPIKey

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
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
    LocationSerializer,
    ArtistSerializer,
    KeywordSerializer,
    ArtworkSerializer,
ThumbnailSerializer,
MembershipSerializer,
CollectionSerializer,

)


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


class ArtworksCollectionViewSet(viewsets.ViewSet):
    """
    list_folders:
    List of all the users workbooks /folders (in anticipation that there will be folders later)

    list_workbooks:
    GET all the users workbooks. #todo define

    retrieve_workbook:
    GET /workbooks/{id}

    retrieve_slides_per_workbook:
    GET /workbooks/{id}/slides LIST (GET) endpoint   # todo??

    edit_slides:
    POST /workbooks/{id}/slides
    Reorder Slides
    Separate_slides
    Reorder artworks within slides

    create_folder:
    POST

    update_workbook:
    PATCH

    delete_workbook:
    DELETE



    """

    serializer_class = CollectionSerializer
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
        List of all the users workbooks /folders (in anticipation that there will be folders later)
        '''
        dummy_data = [{
            'title': 'Some title',
            'ID': 1111,
            'shared_info': 'Some shared info',
            '# of works': 89,
            'thumbnail': 'https://www.thumbnail.com'
        }]
        # WIP todo
        serializer = CollectionSerializer(self.queryset, many=True)
        return Response(dummy_data)

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def list_workbooks(self, request, *args, **kwargs):
        '''
        List of all Workbooks (used for getting latest Workbooks) /workbooks
        '''
        serializer = CollectionSerializer(self.queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_workbook(self, request, workbook_id=None):   # TODO update
        '''
        List of Works (Slides) in a specific Workbook /workbooks/{id}
        '''
        dummy_data = [{
            'title': 'Some workbook title',
            'ID': 1231,
            'shared_info': 'Some shared info',
            'slides': ['SlideObj1', 'SlideObj2'],
        }]
        # todo 2 update serializer once the model is set

        # todo 3
        # - Search works (but only limited results compared to general search - limited to title and artist?)
        # (just have additional param fields in /search  route to indicate which fields should be searched ? -->
        # use /artworks but also need info on is it part of workbook already

        # - Download workbook with slides  - usually needs to take more detailed settings like language,
        # which entry details to include) /workbook/{id}/download ? definite in version version: language,
        # file type + image metadata (title, artist - current status)
        try:
            workbook = ArtworkCollection.objects.get(pk=workbook_id)
        except Artwork.DoesNotExist or ValueError:
            return Response(_('Workbook does not exist'), status=status.HTTP_404_NOT_FOUND)

        serializer = ArtworkSerializer(workbook)
        return Response(serializer.data)

    @extend_schema(
        request=serializer_class,
        responses={
            200: OpenApiResponse(description='OK'),
            403: OpenApiResponse(description='Access not allowed'),
            404: OpenApiResponse(description='Not found'),
        },
    )
    def retrieve_slides_per_workbook(self, request, workbook_id=None):
        '''
        /workbooks/{id}/slides LIST (GET) endpoint returns:
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
                description='Desired order or arrangement of slides within workbook, and/or workbooks within slides',
            ),
        ],
        examples=[
            OpenApiExample(
                name='id list',
                value=[[{ 'id': 'abc1' }, { 'id': 'xyz2' }], [{ 'id': 'fgh23' }], [{ 'id': 'jk54' }]]
            )],
        responses={
            200: OpenApiTypes.OBJECT,
        }
    )
    def edit_slides(self, request, *args, **kwargs):
        '''
        /workbooks/{id}/slides
        Reorder Slides
        Separate_slides
        Reorder artworks within slides
        '''

        # Todo
        # how to submit reorder request? array of order or complete objects? --> just send ids (response: complete object with flag nested info)

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
    #
    # @extend_schema(
    #     methods=['PUT'],
    #     parameters=[
    #         OpenApiParameter(
    #             name='',
    #             type=OpenApiTypes.STR,
    #             required=False,
    #             description='',
    #         ),
    #     ],
    # )
    # def separate_slides(self, request, *args, **kwargs):
    #     '''
    #     Separate Slides /workbooks/{id}/slides
    #     '''
    #     # todo
    #     return Response(
    #         _('No'), status=status.HTTP_404_NOT_FOUND
    #     )
    #
    # @extend_schema(
    #     methods=['PUT'],
    #     parameters=[
    #         OpenApiParameter(
    #             name='slides_id_order',
    #             type=OpenApiTypes.STR,
    #             required=False,
    #             description='Desired order of slides within workbook',
    #         ),
    #     ],
    # )
    # def reorder_slides(self, request, *args, **kwargs):
    #     '''
    #     Reorder Slides /workbooks/{id}/slides
    #     '''
    #     # todo
    #     # Use same approach as reorder_artworks_within_slides (?)
    #
    #     try:
    #         # Find current order of slides ids
    #         # Get suggested order
    #         # make sure it is the right data type
    #         # Match the two according to the suggested order
    #
    #         # order by pk given
    #         dummy_data = [{
    #         'title': 'Some slides title 1',
    #         'artist': 'Joe Jonas',
    #         'image': 'https://www.thumbnail.com/imageid234',
    #         'quick_info': 'Some quick info',
    #         # query flag nested info?
    #         },
    #         {
    #         'title': 'Some slides title 2',
    #         'artist': 'Joe Ponas',
    #         'image': 'https://www.thumbnail.com/imageid234',
    #         'quick_info': 'Some quick info',
    #         # query flag nested info?
    #         }]
    #
    #         # data = {key: i for i, key in enumerate(artworks_id_order)}
    #
    #         return Response(dummy_data)
    #     except:
    #         return Response(
    #             _('Could not reorder slides within workbook'), status=status.HTTP_404_NOT_FOUND
    #         )

    # @extend_schema(
    #     methods=['PUT'],
    #     parameters=[
    #         OpenApiParameter(
    #             name='artworks_id_order',
    #             type=OpenApiTypes.STR,
    #             required=True,
    #             description='Workbook ids order within slide',
    #         ),
    #     ],
    # )
    # def reorder_artworks_within_slide(self, request, *args, **kwargs):
    #     # slide_id=None, artworks_id_order=None
    #     '''
    #     Reorder artworks within a slide /workbooks/{id}/slides
    #     '''
    #     # todo
    #     # slides will be implemented in the model as JSON field ([[]])
    #     # how to submit reorder request? array of order or complete objects?
    #     # --> just send ids (response complete object with flag nested info)
    #     try:
    #         # Find current order of artwork ids
    #         # Get suggested order
    #         # make sure it is the right data type
    #         # Match the two according to the suggested order
    #
    #         # order by pk given
    #         dummy_data = [
    #             {
    #                 "title": "",
    #                 "title_english": "",
    #                 "artists": [],
    #                 "location_of_creation": {
    #                     "id": 15,
    #                     "name": "Loc C.a"
    #                 },
    #                 "location_current": {
    #                     "id": 11,
    #                     "name": "Location A.a.a"
    #                 },
    #                 "date": "",
    #                 "material": "",
    #                 "dimensions": "",
    #                 "keywords": [],
    #                 "description": "",
    #                 "credits": "",
    #                 "checked": False,
    #                 "published": False
    #             },
    #             {
    #                 "title": "",
    #                 "title_english": "",
    #                 "artists": [],
    #                 "location_of_creation": {
    #                     "id": 15,
    #                     "name": "Loc C.a"
    #                 },
    #                 "location_current": {
    #                     "id": 11,
    #                     "name": "Location A.a.a"
    #                 },
    #                 "date": "",
    #                 "material": "",
    #                 "dimensions": "",
    #                 "keywords": [],
    #                 "description": "",
    #                 "credits": "",
    #                 "checked": False,
    #                 "published": False
    #             },
    #
    #         ]
    #
    #         # data = {key: i for i, key in enumerate(artworks_id_order)}
    #
    #         return Response(dummy_data)
    #     except:
    #         return Response(
    #             _('Could not reorder artworks within slide'), status=status.HTTP_404_NOT_FOUND
    #         )

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
        Create Folder /workbooks/{id}
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

    @extend_schema(
        methods=['PATCH']
    )
    def update_workbook(self, request, partial=False, workbook_id=None, *args, **kwargs):
        # TODO patch vs post
        '''
        Update Workbook /workbooks/{id}
        '''
        try:
            workbook = ArtworkCollection.objects.get(pk=workbook_id)
            serializer = CollectionSerializer(data=request.data)

            if serializer.is_valid():
                if serializer.validated_data:
                    workbook.__dict__.update(serializer.validated_data)
                    workbook.save()
                    return Response(serializer.data)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQ)

        except ArtworkCollection.DoesNotExist:
            return Response(_('Workbook does not exist '), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        methods=['DELETE'],
    )
    def delete_workbook(self, request, workbook_id=None, *args, **kwargs):
        '''
        Delete Workbook /workbooks/{id}
        '''
        try:
            workbook = ArtworkCollection.objects.get(pk=workbook_id)
            workbook.delete()
        except ArtworkCollection.DoesNotExist or ValueError:
            return Response(_('Workbook does not exist'), status=status.HTTP_404_NOT_FOUND)

    # todo from Shared INFO / workbook
    # part of workbook model as a many


class UserViewSet(viewsets.GenericViewSet):
    # todo update. and user for artworks, etc
    # serializer_class = UserSerializer

    @extend_schema(
        tags=['user'],
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            dummy_data = {
                'uuid': request.user.username,
                'name': request.user.get_full_name(),
                'email': request.user.email,
            }
            return Response(dummy_data)
        except AttributeError:
            return Response(
                _('User does not exist or is not logged in.'), status=status.HTTP_404_NOT_FOUND
            )
