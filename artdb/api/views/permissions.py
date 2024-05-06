from artworks.models import PermissionsRelation
from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.response import Response

from django.conf import settings


@extend_schema(tags=['permissions'])
class PermissionsViewSet(viewsets.GenericViewSet):
    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    def list(self, request, *args, **kwargs):
        ret = []
        for permission_type in PermissionsRelation.PERMISSION_CHOICES:
            permission = {
                'id': permission_type[0],
                'label': permission_type[1],
            }
            if permission_type[0] in settings.DEFAULT_PERMISSIONS:
                permission['default'] = True
            ret.append(permission)
        return Response(ret)
