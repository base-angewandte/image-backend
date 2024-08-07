from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.template.loader import render_to_string
from django.utils.translation import get_language


class TosViewSet(viewsets.GenericViewSet):
    @extend_schema(
        tags=['tos'],
        responses={
            200: OpenApiResponse(description='OK'),
            404: ERROR_RESPONSES[403],
        },
    )
    @action(detail=False, methods=['post'])
    def accept(self, request, *args, **kwargs):
        """Accept the terms of service.

        This endpoint sets the user's 'tos_accepted' field to 'true'.
        """
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
        """Retrieve the terms of service and status of acceptance.

        This endpoint returns the current 'tos_accepted' and 'tos_text'
        content of the user.
        """
        user = request.user
        tos_accepted = user.tos_accepted
        current_language = get_language()
        if current_language == 'de':
            template_name = 'accounts/terms_of_service_de.html'
        else:
            template_name = 'accounts/terms_of_service_en.html'
        tos_text = render_to_string(template_name, context=None)
        return Response(
            {'tos_accepted': tos_accepted, 'tos_text': tos_text},
            status=status.HTTP_200_OK,
        )
