import logging
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db.models import Q
from artworks.models import ArtworkCollection, Artwork, Artist, Keyword, Location

from api.serializers import LocationSerializer

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
]


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


type_parameter = OpenApiParameter(
    name='type_parameter',
    type=OpenApiTypes.STR,
    required=True,
    location=OpenApiParameter.QUERY,
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


@extend_schema(
    tags=['autocomplete'],
    parameters=[limit],  # TODO type_parameter?, type?
    operation_id='autocomplete_v1_lookup',
)
@api_view(['GET'])
def autocomplete_search(request, type_param='', searchstr='', *args, **kwargs):
    limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
    # TODO:
    #  type_parameter = int(request.GET.get('type_parameter')) if request.GET.get('type_parameter') else None

    items = []
    TYPES = {
        'artworks': {},
        'users': autocomplete_user(request, searchstr),
        'albums': ArtworkCollection.objects.filter(title__icontains=searchstr),
        'title': Artwork.objects.filter(title__icontains=searchstr),  # meaning title of artworks
        'artist': Artist.objects.filter(name__icontains=searchstr),
        'keywords': Keyword.objects.filter(name__icontains=searchstr),
        # TODO fix lookups for locations
        'origin': Location.objects.filter(name__icontains=searchstr),
        'location': Location.objects.filter(name__icontains=searchstr)
    }

    data = TYPES[type_param].values()

    if type_param in 'users':
        if limit and data:
            data = data[0:limit]
        return Response(data)

    if type_param in 'artworks':
        data = [{
            'title': [data_item for data_item in TYPES['title'].values()],
            'artist': [data_item for data_item in TYPES['artist'].values()],
            'keywords': [data_item for data_item in TYPES['keywords'].values()],
            'origin': [data_item for data_item in TYPES['origin'].values()],
            'location': [data_item for data_item in TYPES['location'].values()],
        }]
        return Response(data)

    for data_item in data:
        try:
            items.append(
                data_item
            )
        except AttributeError:
            items.append(
                data_item
            )

    if limit and items:
        items = items[0:limit]

    # TODO: update serializer
    serializer = LocationSerializer(items, many=True)
    return Response(items, status=200)
