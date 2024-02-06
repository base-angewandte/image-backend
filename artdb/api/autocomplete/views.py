from artworks.models import PermissionsRelation
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError
from django.db.models import Q

from .serializers import SOURCES, AutocompleteRequestSerializer


@extend_schema(
    parameters=[
        AutocompleteRequestSerializer,
        OpenApiParameter(
            name='type',
            type={'type': 'array', 'items': {'type': 'string', 'enum': SOURCES}},
            location=OpenApiParameter.QUERY,
            required=True,
            style='form',
            explode=False,
        ),
    ],
    request=AutocompleteRequestSerializer,
    # responses=AutocompleteResponseSerializer,
)
@api_view(['GET'])
def autocomplete(request, *args, **kwargs):
    serializer = AutocompleteRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    limit = serializer.validated_data['limit']
    type_list = serializer.validated_data['type'].split(',')
    q_param = serializer.validated_data['q']

    ret = []

    for t in type_list:
        d = {f'{t}': []}
        if t in ['users', 'permissions']:
            if t == 'users':
                data = autocomplete_user(request, q_param)
                if limit and data:
                    data = autocomplete_user(request, q_param)[0:limit]
                d.get(t).append(data)

            if t == 'permissions':
                data = []
                for permission_type in PermissionsRelation.PERMISSION_CHOICES:
                    data.append(
                        {
                            'id': permission_type[0],
                            'default': settings.PERMISSIONS_DEFAULT.get(
                                permission_type[0]
                            ),
                        }
                    )
                data = data[0:limit]
                d.get(t).append(data)

            ret.append(d)

        else:
            model_map = {
                'albums': 'Album',
                'title': 'Artwork',
                'artist': 'Artist',
                'keywords': 'Keyword',
                'origin': 'Location',
                'location': 'Location',
            }

            try:
                data = apps.get_model('artworks', model_map[t]).objects.filter(
                    name__icontains=q_param
                )[0:limit]
            except FieldError:
                data = apps.get_model('artworks', model_map[t]).objects.filter(
                    title__icontains=q_param
                )[0:limit]

            for data_item in data:
                if t == 'albums' or t == 'title':
                    data_item = {
                        'id': data_item.id,
                        'value': data_item.title,
                    }
                else:
                    data_item = {
                        'id': data_item.id,
                        'value': data_item.name,
                    }
                d.get(t).append(data_item)

            ret.append(d)

            if limit and ret:
                ret = ret[0:limit]

    return Response(ret, status=status.HTTP_200_OK)


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
