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

from angewandte_auth.backend import AngewandteLDAPBackend
from api.spectacular import language_header_parameter
from core.skosmos import autosuggest

logger = logging.getLogger(__name__)

fieldname_parameter = OpenApiParameter(
    name='fieldname',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
    enum=list(settings.ACTIVE_SOURCES.keys()),
)

user = OpenApiParameter(
    name='user',
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    required=True,
)


@extend_schema(
    tags=['autosuggest'],
    parameters=[fieldname_parameter, language_header_parameter],
    operation_id='autosuggest_v1_lookup_all',
)
@api_view(['GET'])
def lookup_view(request, fieldname, *args, **kwargs):
    source = settings.ACTIVE_SOURCES.get(fieldname, ())

    if isinstance(source, dict):
        source = source.get('all', ())

    if isinstance(source, str):
        data = import_string(source)()
    else:
        data = fetch_responses('', source)
    return Response(data)


@extend_schema(
    tags=['autosuggest'],
    parameters=[fieldname_parameter, language_header_parameter],
    operation_id='autosuggest_v1_lookup',
)
@api_view(['GET'])
def lookup_view_search(request, fieldname, searchstr='', *args, **kwargs):
    source = settings.ACTIVE_SOURCES.get(fieldname, ())

    if isinstance(source, dict):
        source = source.get('search', ())

    if isinstance(source, str):
        data = autosuggest(import_string(source)(), searchstr)
    else:
        data = fetch_responses(searchstr, source)

    return Response(data)


@extend_schema(
    tags=['autosuggest'],
    parameters=[user],
    operation_id='autosuggest_user_all',
)
@api_view(['GET'])
def autosuggest_user(request, searchstr='', *args, **kwargs):
    """Get autosuggest results for query."""
    ldap = AngewandteLDAPBackend()
    UserModel = get_user_model()
    source = settings.AUTOSUGGEST_USER_SOURCE
    r = []

    if not settings.AUTOSUGGEST_USER_SOURCE:
        source = 'user_model'

    if 'ldap' in source:
        r = ldap.search_users_by_name(searchstr)

    elif 'user_model' in source:
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

    return Response(r)


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
