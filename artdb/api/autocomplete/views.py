from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import SOURCES, AutocompleteRequestSerializer

MODEL_MAP = {
    'albums': 'Album',
    'titles': 'Artwork',
    'artists': 'Artist',
    'keywords': 'Keyword',
    'origins': 'Location',
    'locations': 'Location',
}


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
        if t == 'users':
            data = autocomplete_user(request, q_param)
            if limit and data:
                data = autocomplete_user(request, q_param)[:limit]
            d.get(t).append(data)

        elif t in ['albums', 'titles']:
            data = apps.get_model('artworks', MODEL_MAP[t]).objects.filter(
                title__icontains=q_param
            )[:limit]

            for item in data:
                d[t].append(
                    {
                        'id': item.id,
                        'value': item.title,
                    }
                )
        else:
            data = apps.get_model('artworks', MODEL_MAP[t]).objects.filter(
                name__icontains=q_param
            )[:limit]

            for item in data:
                d[t].append(
                    {
                        'id': item.id,
                        'value': item.name,
                    }
                )

        ret.append(d)

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
