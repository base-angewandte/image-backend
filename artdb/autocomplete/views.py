import logging
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from django.db.models import Q
from artworks.models import Album, Artwork, Artist, Keyword, Location, PermissionsRelation

from artdb.settings import PERMISSIONS_DEFAULT
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

SOURCES = [
    'artworks',
    'users',
    'albums',
    'title',
    'artist',
    'keywords',
    'origin',
    'location',
    'permissions'
]

searchstring_parameter = OpenApiParameter(
    name='searchstr',
    type=OpenApiTypes.STR,
    required=False,
    description='',
    # default=''
)

type_parameter = OpenApiParameter(
    name='type_parameter',
    type=OpenApiTypes.STR,
    required=True,
    enum=SOURCES,
)

limit = OpenApiParameter(
    name='limit',
    type=OpenApiTypes.INT,
    required=False,
    description='',
)

user = OpenApiParameter(
    name='user',
    type=OpenApiTypes.STR,
    required=True,
)


def autocomplete_user(request, searchstr=''):
    """Get autocomplete results for query."""
    UserModel = get_user_model()
    search_result = UserModel.objects.filter(
        Q(first_name__icontains=searchstr) | Q(last_name__icontains=searchstr)
    )
    r = []
    for user in search_result:
        r.append(
            {
                'UUID': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'label': f'{user.first_name} {user.last_name}',
            },
        )
    return r


@extend_schema(
    tags=['autocomplete'],
    parameters=[limit, type_parameter, searchstring_parameter],
    operation_id='autocomplete_v1_lookup',

)
@api_view(['GET'])
def autocomplete_search(request, *args, **kwargs):
    try:
        limit = int(request.GET.get('limit')) if request.GET.get('limit') else 10  # default
        type_parameter = request.GET.get('type_parameter') if request.GET.get('type_parameter') else 'artworks'


        # Todo In progress after review

        # if not isinstance(limit), int):
        #     return Response(_('Limit must be an integer.'), status=status.HTTP_400_BAD_REQUEST)

        # if type_parameter not in SOURCES:
        #     return Response(_(f'The type_parameter must be one of the following: {"".join(SOURCES)}.'), status=status.HTTP_400_BAD_REQUEST)

        searchstr = request.GET.get('searchstr', '')

        items = []
        TYPES = {
            'artworks': {},
            'users': autocomplete_user(request, searchstr),
            'albums': Album.objects.filter(title__icontains=searchstr),
            'title': Artwork.objects.filter(title__icontains=searchstr),  # meaning title of artworks
            'artist': Artist.objects.filter(name__icontains=searchstr),
            'keywords': Keyword.objects.filter(name__icontains=searchstr),
            'origin': Location.objects.filter(name__icontains=searchstr),
            'location': Location.objects.filter(name__icontains=searchstr),
        }

        if type_parameter == 'users':
            data = TYPES[type_parameter]
            if limit and data:
                data = TYPES[type_parameter][0:limit]
            return Response(data)

        if type_parameter == 'permissions':
            data = []
            for permission_type in PermissionsRelation.PERMISSION_CHOICES:
                data.append({
                        "id": permission_type[0],
                        "default": PERMISSIONS_DEFAULT.get(permission_type[0])
                    })
            data = data[0:limit]
            return Response(data)

        data = TYPES[type_parameter].values()

        if type_parameter == 'artworks':
            data = [{
                'title': [data_item for data_item in TYPES['title'].values()],
                'artist': [data_item for data_item in TYPES['artist'].values()],
                'keywords': [data_item for data_item in TYPES['keywords'].values()],
                'origin': [data_item for data_item in TYPES['origin'].values()],
                'location': [data_item for data_item in TYPES['location'].values()],
            }]
            data = data[0:limit]
            return Response(data)

        for data_item in data:
            if type_parameter in 'albums' or type_parameter in 'title':
                data_item = {
                    'id': data_item.get('id'),
                    'value': data_item.get('title')
                }
            else:
                data_item = {
                    'id': data_item.get('id'),
                    'value': data_item.get('name')
                }
            try:
                items.append(
                    data_item
                )
            except AttributeError:
                print("whgwzgw")
                items.append(
                    data_item
                )
        if limit and items:
            print("ok if limit")
            # print(items)
            # print(limit)
            print(type(limit))
            print(items[0:limit])
            items = items[0:limit]
            print("!!!!")

    except Exception: # todo
        return Response(
            _('Nope', status.HTTP_400_BAD_REQUEST)
        )

    print("about to return")
    return Response(items, status=200)
