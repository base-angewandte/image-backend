from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _

from artworks.models import (
    Album,
    Artist,
    Artwork,
    Keyword,
    Location,
    PermissionsRelation,
)

from .serializers import (
    SOURCES,
    AutocompleteRequestSerializer,
    AutocompleteResponseIntegerIdSerializer,
    AutocompleteResponseItemIntegerIdSerializer,
    AutocompleteResponseItemSerializer,
    AutocompleteResponseSerializer,
)

MODEL_MAP = {
    'user_albums_editable': Album,
    'titles': Artwork,
    'artists': Artist,
    'keywords': Keyword,
    'locations': Location,
    'users': get_user_model(),
}

LABELS_MAP = {
    'user_albums_editable': _('autocomplete_user_albums_editable'),
    'titles': _('autocomplete_titles'),
    'artists': _('autocomplete_artists'),
    'keywords': _('autocomplete_keywords'),
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
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description='A JSON array containing the autocomplete results',
            response=PolymorphicProxySerializer(
                component_name='AutocompleteResult',
                serializers=[
                    AutocompleteResponseSerializer(many=True),
                    AutocompleteResponseItemSerializer(many=True),
                    AutocompleteResponseIntegerIdSerializer(many=True),
                    AutocompleteResponseItemIntegerIdSerializer(many=True),
                ],
                resource_type_field_name=None,
                many=False,
            ),
            examples=[
                OpenApiExample(
                    name='single type response',
                    value=[
                        {
                            'id': 'id1',
                            'label': 'Robin Smith',
                        },
                        {
                            'id': 'id2',
                            'label': 'Max Smith',
                        },
                    ],
                ),
                OpenApiExample(
                    name='multiple types response',
                    value=[
                        {
                            'id': 'users',
                            'label': 'Users',
                            'data': [
                                {
                                    'id': 'id1',
                                    'label': 'Max Smith',
                                },
                                {
                                    'id': 'id2',
                                    'label': 'Robin Smith',
                                },
                            ],
                        },
                        {
                            'id': 'titles',
                            'label': 'Titles',
                            'data': [],
                        },
                    ],
                ),
            ],
        ),
    },
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
            query = (
                MODEL_MAP[t]
                .objects.annotate(
                    name=Concat('first_name', Value(' '), 'last_name'),
                )
                .annotate(
                    similarity=TrigramWordSimilarity(
                        q_param,
                        'name',
                    ),
                )
                .filter(similarity__gte=0.6)
                .order_by('-similarity')
            )
            for user in query:
                d['data'].append(
                    {
                        'id': user.username,
                        'label': user.get_full_name(),
                    },
                )
        elif t == 'user_albums_editable':
            q_filters = Q(user=request.user) | Q(
                pk__in=PermissionsRelation.objects.filter(
                    user=request.user,
                    permissions='EDIT',
                ).values_list('album__pk', flat=True),
            )
            query = (
                MODEL_MAP[t]
                .objects.filter(q_filters)
                .filter(title__icontains=q_param)[:limit]
            )

            for album in query:
                d['data'].append(
                    {
                        'id': album.id,
                        'label': album.title,
                    },
                )

        elif t == 'titles':
            query = MODEL_MAP[t].objects.filter(title__icontains=q_param)[:limit]

            for artwork in query:
                d['data'].append(
                    {
                        'id': artwork.id,
                        'label': artwork.title,
                        'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                    },
                )

        else:
            query = MODEL_MAP[t].objects.filter(name__icontains=q_param)[:limit]

            for item in query:
                d['data'].append(
                    {
                        'id': item.id,
                        'label': item.name,
                    },
                )

        ret.append(d)

    if len(ret) == 1:
        ret = ret[0]['data']

    return Response(ret, status=status.HTTP_200_OK)
