from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .serializers import SOURCES, AutocompleteRequestSerializer

MODEL_MAP = {
    'albums': 'Album',
    'titles': 'Artwork',
    'artists': 'Artist',
    'keywords': 'Keyword',
    'origins': 'Location',
    'locations': 'Location',
}

LABELS_MAP = {
    'albums': _('autocomplete_albums'),
    'titles': _('autocomplete_titles'),
    'artists': _('autocomplete_artists'),
    'keywords': _('autocomplete_keywords'),
    'origins': _('autocomplete_origins'),
    'locations': _('autocomplete_locations'),
    'users': _('autocomplete_users'),
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
        d = {
            'id': t,
            'label': LABELS_MAP[t],
            'data': [],
        }

        if t == 'users':
            UserModel = get_user_model()
            query = UserModel.objects.filter(
                Q(first_name__icontains=q_param) | Q(last_name__icontains=q_param)
            )[:limit]
            for user in query:
                d['data'].append(
                    {
                        'id': user.username,
                        'label': user.get_full_name(),
                    },
                )
        elif t in ['albums', 'titles']:
            data = apps.get_model('artworks', MODEL_MAP[t]).objects.filter(
                title__icontains=q_param
            )[:limit]

            for item in data:
                d['data'].append(
                    {
                        'id': item.id,
                        'label': item.title,
                    }
                )
        else:
            data = apps.get_model('artworks', MODEL_MAP[t]).objects.filter(
                name__icontains=q_param
            )[:limit]

            for item in data:
                d['data'].append(
                    {
                        'id': item.id,
                        'label': item.name,
                    }
                )

        ret.append(d)

    if len(ret) == 1:
        ret = ret[0]['data']

    return Response(ret, status=status.HTTP_200_OK)
