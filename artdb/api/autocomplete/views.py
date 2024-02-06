from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

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

    # limit = serializer.validated_data['limit']
    # type_list = serializer.validated_data['type'].split(',')
    # q_param = serializer.validated_data['q']

    ret = []

    # TODO insert autocomplete code

    return Response(ret, status=status.HTTP_200_OK)
