import json
import logging
from apimapper import APIMapper
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.module_loading import import_string
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
    # ldap = AngewandteLDAPBackend()
    # UserModel = get_user_model()
    # source = settings.AUTOSUGGEST_USER_SOURCE
    # r = []
    #
    # if not settings.AUTOSUGGEST_USER_SOURCE:
    #     source = 'user_model'
    #
    # if 'ldap' in source:
    #     r = ldap.search_users_by_name(searchstr)
    #
    # elif 'user_model' in source:
    #     search_result = UserModel.objects.filter(
    #         Q(first_name__icontains=searchstr) | Q(last_name__icontains=searchstr)
    #     )
    #     r = []
    #     for user in search_result:
    #         r.append(
    #             {
    #                 'UUID': user.username,
    #                 'first_name': user.first_name,
    #                 'last_name': user.last_name,
    #                 'label': f'{user.first_name} {user.last_name}',
    #             },
    #         )
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
    # location=OpenApiParameter.PATH,
    required=True,
)


@extend_schema(
    tags=['autocomplete'],
    parameters=[limit],  # todo type_parameter?, type?
    operation_id='autocomplete_v1_lookup',
)
@api_view(['GET'])
def autocomplete_search(request, type_param='', searchstr='', *args, **kwargs):

    # Todo how to get ahold of limit? by being post???
    # if not post:
    # serializer, object

    #  if limit:
    #       activities = activities[0:limit]
    # Todo 2 maybe find another solution for TYPE that is cleaner

    limit = int(request.GET.get('limit')) if request.GET.get('limit') else None
    type_parameter = int(request.GET.get('type_parameter')) if request.GET.get('type_parameter') else None
    print(limit)
    print(type_parameter)

    items = []
    TYPES = {
        'artworks': {},  # TODO
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


    # Todo: needs more iter?
    if type_param in 'artworks':
        # for item in artwork?
        data = [{
            'title': [data_item for data_item in TYPES['title'].values()],
            'artist': [data_item for data_item in TYPES['artist'].values()],
            'keywords': [data_item for data_item in TYPES['keywords'].values()],
            'origin': [data_item for data_item in TYPES['origin'].values()],
            'location': [data_item for data_item in TYPES['location'].values()],
        }]
        return Response(data)


    # todo OR
    for data_item in data:
        try:
            items.append(
                # {
                #     'id': data_item.id,
                #     'title': data_item.title,
                # }
                data_item
            )
        except AttributeError:
            items.append(
                # {
                #     'id': data_item.id,
                #     'title': data_item.name,
                # }
                data_item
            )

    print(items)
    print(limit)
    if limit and items:
        items = items[0:limit]

    # Todo: web of serializers
    serializer = LocationSerializer(items, many=True)
    return Response(items, status=200)

    # if isinstance(source, dict):
    #     source = source.get('search', ())
    #
    # if isinstance(source, str):
    #     data = autocomplete(import_string(source)(), searchstr)
        # pass
    # else:
    #     data = fetch_responses(searchstr, source)

    # DUMMY
    dummy_data = {
        'title': f'Some {type} Name',
        'artist': 'Artist Name',
        'keywords': 'a, b, c',
        'place_of_production': 'Some Place',
        'current_location': 'Some Location'
    }

    return Response(dummy_data)

    return Response(data)

# s = self.get_serializer(data=request.data)
#         s.is_valid(raise_exception=True)
#         q = s.data.get('q')
#         filter_id = s.data.get('filter_id')
#         limit = s.data.get('limit')
#         lang = request.LANGUAGE_CODE
#
#         items = []
#         # for now the default filter is the same as activities
#         # TODO: change, as soon as we have entities and albums in our test data
#         if filter_id == 'default':
#             filter_id = 'activities'
#         if filter_id == 'activities':
#             activities = Activity.objects.filter(title__icontains=q)
#             if limit:
#                 activities = activities[0:limit]
#             for activity in activities:
#                 items.append(
#                     {
#                         'id': activity.id,
#                         'title': activity.title,
#                         'subtext': activity.subtext,
#                     }
#                 )
#
#         else:
#             return Response(
#                 {
#                     'source': filter_id,
#                     'label': 'This autocomplete filter is not implemented yet',
#                     'data': [],
#                 },
#                 status=200,
#             )
#
#         ret = [
#             {
#                 'source': filter_id,
#                 'label': get_static_filter_label(filter_id, lang),
#                 'data': items,
#             }
#         ]
#         return Response(ret, status=200)





def fetch_responses(querystring, active_sources):
    responses = []
    for src in active_sources:
        api = APIMapper(
            # this is kinda hacky - change it if there's a better solution to force evaluation of lazy objects
            # inside a dict
            json.loads(json.dumps(settings.SOURCES.get(src), cls=JSONEncoder)),
            settings.RESPONSE_MAPS.get(src),
            timeout=2,
        )
        res = api.fetch_results(querystring)
        responses.extend(res)

    return responses
