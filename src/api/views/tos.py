from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.template.loader import render_to_string


class TosViewSet(viewsets.GenericViewSet):
    """
    list:
    GET tos/
    status of tos accepted and text of the html template terms_of_service

    create:
    POST /tos/
    SET tos status to True
    """

    @extend_schema(
        tags=['tos'],
        responses={
            200: OpenApiResponse(description='OK'),
            404: ERROR_RESPONSES[403],
        },
        operation_id='tos_accept',
    )
    @action(detail=False, methods=['post'])
    def accept(self, request, *args, **kwargs):
        user = request.user
        user.tos_accepted = True
        user.save()
        return Response({'tos_accepted': user.tos_accepted}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['tos'],
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    def list(self, request, *args, **kwargs):
        user = request.user
        tos_accepted = user.tos_accepted
        tos_text = render_to_string('accounts/terms_of_service.html', context=None)
        return Response(
            {'tos_accepted': tos_accepted, 'tos_text': tos_text},
            status=status.HTTP_200_OK,
        )
