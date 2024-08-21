import logging
import zipfile
from io import BytesIO

from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from api.serializers.artworks import (
    ArtworksAlbumsRequestSerializer,
    ArtworksImageRequestSerializer,
)
from api.views import (
    check_limit,
    check_offset,
    get_person_list,
    get_person_list_for_download,
)
from artworks.models import Album, Artwork, PermissionsRelation

logger = logging.getLogger(__name__)


@extend_schema(tags=['artworks'])
class ArtworksViewSet(viewsets.GenericViewSet):
    """
    list:
    GET all artworks.

    retrieve:
    GET specific artwork.

    retrieve_albums:
    GET albums the current user has added this artwork to.

    download:
    GET Download artwork + metadata

    """

    queryset = Artwork.objects.filter(published=True)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                required=False,
                default=100,
            ),
            OpenApiParameter(
                name='offset',
                type=OpenApiTypes.INT,
                required=False,
                default=0,
            ),
        ],
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def list(self, request, *args, **kwargs):
        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))

        qs = self.get_queryset()

        total = qs.count()

        qs = qs[offset : offset + limit]

        qs = qs.prefetch_related('artists', 'discriminatory_terms')

        return Response(
            {
                'total': total,
                'results': [
                    {
                        'id': artwork.id,
                        'image_original': request.build_absolute_uri(
                            artwork.image_original.url,
                        )
                        if artwork.image_original
                        else None,
                        'credits': artwork.credits,
                        'title': artwork.title,
                        'date': artwork.date,
                        'artists': get_person_list(artwork.artists.all()),
                        'photographers': get_person_list(artwork.photographers.all()),
                        'authors': get_person_list(artwork.authors.all()),
                        'graphic_designers': get_person_list(
                            artwork.graphic_designers.all(),
                        ),
                        'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                    }
                    for artwork in qs
                ],
            },
        )

    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne
        except ValueError as ve:
            raise ParseError(_('Artwork id must be of type integer')) from ve

        return Response(
            {
                'id': artwork.id,
                'image_original': request.build_absolute_uri(artwork.image_original.url)
                if artwork.image_original
                else None,
                'credits': artwork.credits,
                'license': '',  # placeholder for future field change, see ticket 2070
                'title': artwork.title,
                'title_english': artwork.title_english,
                'title_comment': artwork.title_comment,
                'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                'date': artwork.date,
                'material': artwork.material,
                'dimensions': artwork.dimensions,
                'comments': artwork.comments,
                'place_of_production': {
                    'id': artwork.place_of_production.id,
                    'value': artwork.place_of_production.name,
                }
                if artwork.place_of_production
                else {},
                'location': {
                    'id': artwork.location.id,
                    'value': artwork.location.name,
                }
                if artwork.location
                else {},
                'artists': get_person_list(artwork.artists.all()),
                'photographers': get_person_list(artwork.photographers.all()),
                'authors': get_person_list(artwork.authors.all()),
                'graphic_designers': get_person_list(artwork.graphic_designers.all()),
                'keywords': [
                    {'id': keyword.id, 'value': keyword.name}
                    for keyword in artwork.keywords.all()
                ],
            },
        )

    # additional actions

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='method',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                enum=(
                    'crop',
                    'resize',
                ),
            ),
            OpenApiParameter(
                name='width',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name='height',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
        responses={
            # TODO better response definition
            302: OpenApiResponse(),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='image/(?P<method>[a-z]+)/(?P<width>[0-9]+)x(?P<height>[0-9]+)',
    )
    def image(self, request, pk=None, *args, **kwargs):
        serializer = ArtworksImageRequestSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne
        method = serializer.validated_data['method']
        size = f'{serializer.validated_data["width"]}x{serializer.validated_data["height"]}'
        match method:
            case 'resize':
                url = artwork.image_original.thumbnail[size].url
            case 'crop':
                url = artwork.image_original.crop[size].url
            case _:
                url = artwork.image_original.url
        return redirect(request.build_absolute_uri(url))

    @extend_schema(
        responses={
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    @action(detail=False, methods=['get'])
    def labels(self, request, pk=None, *args, **kwargs):
        ret = {}

        exclude = (
            'id',
            'checked',
            'published',
            'date_created',
            'date_changed',
            'search_vector',
        )

        # Artworks
        fields = Artwork._meta.get_fields()
        for field in fields:
            if field.name not in exclude and hasattr(field, 'verbose_name'):
                ret[field.name] = field.verbose_name

        return Response(ret)

    @extend_schema(
        parameters=[
            ArtworksAlbumsRequestSerializer,
            OpenApiParameter(
                name='permissions',
                type={
                    'type': 'array',
                    'items': {'type': 'string', 'enum': settings.PERMISSIONS},
                },
                location=OpenApiParameter.QUERY,
                required=False,
                style='form',
                explode=False,
                description=(
                    "If the response should also return shared albums, it's possible to define which permissions the "
                    'user needs to have for the album. Since the default is `EDIT`, shared albums with `EDIT` '
                    'permissions are included in the response.'
                ),
                default='EDIT',
            ),
        ],
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=True, methods=['get'], url_path='albums')
    def retrieve_albums(self, request, pk=None, *args, **kwargs):
        serializer = ArtworksAlbumsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        q_filters = Q()

        if serializer.validated_data['owner']:
            q_filters |= Q(user=request.user)

        permissions = serializer.validated_data['permissions'].split(',')

        if permissions:
            q_filters |= Q(
                pk__in=PermissionsRelation.objects.filter(
                    user=request.user,
                    permissions__in=permissions,
                ).values_list('album__pk', flat=True),
            )

        albums = Album.objects.filter(slides__contains=[[{'id': artwork.pk}]]).filter(
            q_filters,
        )

        return Response(
            [
                {
                    'id': album.id,
                    'title': album.title,
                }
                for album in albums
            ],
        )

    @extend_schema(
        responses={
            # TODO better response definition
            #   https://drf-spectacular.readthedocs.io/en/latest/faq.html#how-to-serve-in-memory-generated-files-or-files-in-general-outside-filefield
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
            500: OpenApiResponse(description='Internal Server Error'),
        },
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, *args, **kwargs):
        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        # create metadata file content
        metadata_content = ''
        metadata_content += f'{artwork._meta.get_field("title").verbose_name.title()}: {artwork.title} \n'
        metadata_content += f'{artwork._meta.get_field("title_english").verbose_name.title()}: {artwork.title_english} \n'
        metadata_content += f'{artwork._meta.get_field("title_comment").verbose_name.title()}: {artwork.title_comment} \n'
        metadata_content += get_person_list_for_download(
            artwork.artists.all(),
            _('Artist'),
        )
        metadata_content += get_person_list_for_download(
            artwork.photographers.all(),
            _('Photographer'),
        )
        metadata_content += get_person_list_for_download(
            artwork.authors.all(),
            _('Author'),
        )
        metadata_content += get_person_list_for_download(
            artwork.graphic_designers.all(),
            _('Graphic designers'),
        )
        metadata_content += (
            f'{artwork._meta.get_field("date").verbose_name.title()}: {artwork.date} \n'
        )
        metadata_content += f'{artwork._meta.get_field("material").verbose_name.title()}: {artwork.material} \n'
        metadata_content += f'{artwork._meta.get_field("dimensions").verbose_name.title()}: {artwork.dimensions} \n'
        metadata_content += f'{artwork._meta.get_field("comments").verbose_name.title()}: {artwork.comments} \n'
        metadata_content += f'{artwork._meta.get_field("credits").verbose_name.title()}: {artwork.credits} \n'
        metadata_content += f'{artwork._meta.get_field("keywords").verbose_name.title()}: {", ".join([i.name for i in artwork.keywords.all()])} \n'
        metadata_content += f'{artwork._meta.get_field("location").verbose_name.title()}: {artwork.location if artwork.location else ""} \n'
        metadata_content += f'{artwork._meta.get_field("place_of_production").verbose_name.title()}: {artwork.place_of_production} \n'

        output_zip = BytesIO()

        #  image to zipfile & metadata
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as image_zip:
            artwork_title = slugify(artwork.title)
            image_suffix = artwork.image_original.name.split('.')[-1]

            try:
                image_zip.write(
                    artwork.image_original.path,
                    arcname=f'{artwork_title}.{image_suffix}',
                )
            except FileNotFoundError:
                error_info = _('File for artwork {pk} not found')
                logger.exception(error_info.format(pk=pk))
                return Response(
                    error_info.format(pk=pk),
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            image_zip.writestr(f'{artwork_title}_metadata.txt', metadata_content)
            image_zip.close()

            return HttpResponse(
                output_zip.getvalue(),
                content_type='application/x-zip-compressed',
                headers={
                    'Content-Disposition': f'attachment; filename={artwork_title}.zip',
                },
            )
