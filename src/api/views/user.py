from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import extend_schema
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
        'tos_accepted': request.user.tos_accepted,
    }
    return Response(ret, status=200)
