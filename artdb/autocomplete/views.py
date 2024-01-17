import logging
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Q
from artworks.models import Album, Artwork, Artist, Keyword, Location, PermissionsRelation
from django.core.exceptions import FieldError
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

query = OpenApiParameter(
    name='query',
    type=OpenApiTypes.STR,
    required=False,
)

type = OpenApiParameter(
    name='type',
    type=OpenApiTypes.STR,
    required=True,
    description=f'choose between {", ".join(SOURCES)}, only one at a time allowed.',
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
    parameters=[limit, type, query],
    operation_id='autocomplete_v1_lookup',

)
@api_view(['GET'])
def autocomplete_search(request, *args, **kwargs):
    try:
        limit = int(request.GET.get('limit')) if request.GET.get('limit') else 10  # default
        type_parameter = request.GET.get('type') if request.GET.get('type') else 'artworks'

        if not isinstance((limit), int):
            return Response(_('Limit must be an integer.'), status=status.HTTP_400_BAD_REQUEST)

        if type_parameter not in SOURCES:
            return Response(_(f'The type_parameter must be one of the following: {", ".join(SOURCES)}.'), status=status.HTTP_400_BAD_REQUEST)

        searchstr = request.GET.get('searchstr', '')

        items = []

        if type_parameter == 'users':
            data = autocomplete_user(request, searchstr)
            if limit and data:
                data = autocomplete_user(request, searchstr)[0:limit]
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

        if type_parameter == 'artworks':
            data = [{
                'title': [data_item for data_item in
                          Artwork.objects.filter(title__icontains=searchstr)[0:limit].values()],
                # meaning title of artworks
                'artist': [data_item for data_item in
                           Artist.objects.filter(name__icontains=searchstr)[0:limit].values()],
                'keywords': [data_item for data_item in
                             Keyword.objects.filter(name__icontains=searchstr)[0:limit].values()],
                'origin': [data_item for data_item in
                           Location.objects.filter(name__icontains=searchstr)[0:limit].values()],
                'location': [data_item for data_item in
                             Location.objects.filter(name__icontains=searchstr)[0:limit].values()],
            }]
            data = data[0:limit]
            return Response(data)

        model_map = {
            'albums': 'Album',
            'title': 'Artwork',
            'artist': 'Artist',
            'keywords': 'Keyword',
            'origin': 'Location',
            'location': 'Location',
        }

        try:
            data = apps.get_model('artworks', model_map[type_parameter]).objects.filter(name__icontains=searchstr)[0:limit]
        except FieldError:
            data = apps.get_model('artworks', model_map[type_parameter]).objects.filter(title__icontains=searchstr)[0:limit]

        for data_item in data:
            if type_parameter == 'albums' or type_parameter == 'title':
                print(data_item)
                data_item = {
                    'id': data_item.id,
                    'value': data_item.title
                }
            else:
                data_item = {
                    'id': data_item.id,
                    'value': data_item.name
                }
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

    except Exception as e:
        return Response(
            _(f'{e}'), status.HTTP_400_BAD_REQUEST
        )

    return Response(items, status=200)
