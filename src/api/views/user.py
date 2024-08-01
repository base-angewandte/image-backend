from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers.user import TosAcceptedSerializer, UserDataSerializer


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
        'tos_accepted': request.user.tos_accepted,
    }
    return Response(ret, status=200)


@extend_schema(
    tags=['user'],
    request=TosAcceptedSerializer,
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
    ],
)
@api_view(['POST'])
def post_tos_accepted(request, *args, **kwargs):
    serializer = TosAcceptedSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    tos_accepted_user_bool = serializer.validated_data['tos_accepted']
    user = request.user
    current_tos_on_server_accepted = user.tos_accepted
    # If tos_accepted is True on the server
    if current_tos_on_server_accepted:
        # User wants to accept TOS again, just confirm it's already True
        if tos_accepted_user_bool:
            return Response({'tos_accepted': True}, status=200)
        # User tries to decline TOS after accepting it, which is not allowed
        else:
            return Response(
                {
                    'error': 'Cannot decline terms of service,'
                    'please send us an email to assist you further',
                },
                status=400,
            )
    # If none of the above are the case, just save the user's decision
    user.tos_accepted = tos_accepted_user_bool
    user.save()
    return Response({'tos_accepted': tos_accepted_user_bool}, status=200)
