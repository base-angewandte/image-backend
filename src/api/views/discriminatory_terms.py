from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from artworks.models import DiscriminatoryTerm


@extend_schema(
    tags=['discriminatory_terms'],
    responses={
        200: OpenApiResponse(
            description='A list of discriminatory terms, which should be contextualised.',
        ),
    },
)
@api_view(['get'])
def discriminatory_terms(request, *args, **kwargs):
    return Response(list(DiscriminatoryTerm.objects.values_list('term', flat=True)))
