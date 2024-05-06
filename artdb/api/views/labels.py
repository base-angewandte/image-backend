from artworks.models import Artwork
from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.response import Response


@extend_schema(tags=['labels'])
class LabelsViewSet(viewsets.GenericViewSet):
    """
    list:
    GET labels
    """

    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        ret = {}

        exclude = (
            'id',
            'created_at',
            'updated_at',
            'checked',
            'published',
        )

        # Artworks
        fields = Artwork._meta.get_fields()
        for field in fields:
            if field.name not in exclude and hasattr(field, 'verbose_name'):
                ret[field.name] = field.verbose_name

        return Response(ret)
