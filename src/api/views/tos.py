from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.conf import settings
from django.utils.translation import get_language

from texts.models import Text


@extend_schema(tags=['tos'])
class TosViewSet(viewsets.GenericViewSet):
    @extend_schema(
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
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    def list(self, request, *args, **kwargs):
        """Retrieve the terms of service and status of acceptance for the
        current user."""

        current_language = get_language() or settings.LANGUAGE_CODE

        return Response(
            {
                'tos_accepted': request.user.tos_accepted,
                'tos_text': getattr(Text.objects.get(pk=1), current_language, ''),
            },
            status=status.HTTP_200_OK,
        )
