from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers.user import UserDataSerializer


@extend_schema(
    tags=['user'],
    responses={
        200: UserDataSerializer,
        401: ERROR_RESPONSES[401],
    },
)
@api_view(['GET'])
def get_user_data(request, *args, **kwargs):
    attributes = request.session.get('attributes', {})
    ret = {
        'id': request.user.username,
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'showroom_id': attributes.get('showroom_id'),
        'groups': attributes.get('groups'),
        'permissions': attributes.get('permissions'),
        'tos_accepted': attributes.get('tos_accepted'),
    }
    return Response(ret, status=200)


@extend_schema(
    tags=['user'],
    parameters=[
        OpenApiParameter(
            name='tos_accepted',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The user's TOS accepted status",
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: ERROR_RESPONSES[400],
    },
    examples=[
        OpenApiExample(
            'Accept TOS',
            description='Example for accepting the terms of service',
            value={'tos_accepted': True},
        ),
        OpenApiExample(
            'Decline TOS',
            description='Example for declining the terms of service',
            value={'tos_accepted': False},
        ),
    ],
)
@api_view(['POST'])
def post_tos_accepted(request, *args, **kwargs):
    tos_accepted = request.query_params.get('tos_accepted', None)
    if tos_accepted is None:
        return Response({'error': 'tos_accepted parameter is missing.'}, status=400)
    try:
        tos_accepted_bool = tos_accepted.lower() == 'true'
    except AttributeError:
        return Response(
            {'error': "Invalid value for tos_accepted. Must be 'true' or 'false'."},
            status=400,
        )
    attributes = request.session.get('attributes', {})
    attributes['tos_accepted'] = tos_accepted_bool
    request.session['attributes'] = attributes
    return Response({'tos_accepted': tos_accepted_bool}, status=200)
