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
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import get_language, gettext_lazy as _

from api.serializers.artworks import (
    ArtworksAlbumsRequestSerializer,
    ArtworksImageRequestSerializer,
)
from api.views import (
    check_limit,
    check_offset,
    get_person_list,
)
from artworks.models import Album, Artwork, PermissionsRelation
from texts.models import Text

logger = logging.getLogger(__name__)


@extend_schema(tags=['artworks'])
class ArtworksViewSet(viewsets.GenericViewSet):
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
        """List of Artworks."""

        limit = check_limit(request.query_params.get('limit', 100))
        offset = check_offset(request.query_params.get('offset', 0))

        qs = self.get_queryset()

        total = qs.count()

        qs = qs[offset : offset + limit]

        qs = qs.prefetch_related(
            'artists',
            'photographers',
            'authors',
            'graphic_designers',
            'discriminatory_terms',
        )

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
                        'image_fullsize': request.build_absolute_uri(
                            artwork.image_fullsize.url,
                        )
                        if artwork.image_fullsize
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
    def retrieve(self, request, *args, pk=None, **kwargs):
        """Retrieve information for a specific Artwork."""

        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        return Response(
            {
                'id': artwork.id,
                'image_original': request.build_absolute_uri(artwork.image_original.url)
                if artwork.image_original
                else None,
                'image_fullsize': request.build_absolute_uri(artwork.image_fullsize.url)
                if artwork.image_fullsize
                else None,
                'title': artwork.title,
                'title_english': artwork.title_english,
                'title_comment': artwork.title_comment_localized,
                'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                'date': artwork.date,
                'material': artwork.material_description_localized,
                'dimensions': artwork.dimensions_display,
                'comments': artwork.comments_localized,
                'credits': artwork.credits,
                'credits_link': artwork.credits_link,
                'link': artwork.link,
                'license': getattr(Text.objects.get(pk=2), get_language(), ''),
                'place_of_production': artwork.get_place_of_production_list(),
                'location': {
                    'id': artwork.location.id,
                    'value': artwork.location.name_localized,
                }
                if artwork.location
                else {},
                'artists': get_person_list(artwork.artists.all()),
                'photographers': get_person_list(artwork.photographers.all()),
                'authors': get_person_list(artwork.authors.all()),
                'graphic_designers': get_person_list(artwork.graphic_designers.all()),
                'keywords': [
                    {
                        'id': keyword.id,
                        'value': keyword.name_localized,
                    }
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
    def image(self, request, *args, pk=None, **kwargs):
        """Get a cropped or resized thumbnail for an Artwork image."""

        serializer = ArtworksImageRequestSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)

        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        if artwork.image_original and not artwork.image_fullsize:
            artwork.create_image_fullsize()

        method = serializer.validated_data['method']
        size = f'{serializer.validated_data["width"]}x{serializer.validated_data["height"]}'

        match method:
            case 'resize':
                url = artwork.image_fullsize.thumbnail[size].url
            case 'crop':
                url = artwork.image_fullsize.crop[size].url
            case _:
                url = artwork.image_fullsize.url

        return redirect(request.build_absolute_uri(url))

    @extend_schema(
        responses={
            # TODO better response definition
            200: OpenApiResponse(description='OK'),
            403: ERROR_RESPONSES[403],
        },
    )
    @action(detail=False, methods=['get'])
    def labels(self, request, *args, **kwargs):
        """Get all labels for displaying Artwork metadata."""

        ret = {}

        exclude = (
            'id',
            'checked',
            'published',
            'date_created',
            'date_changed',
            'search_persons',
            'search_locations',
            'search_keywords',
            'search_materials',
            'search_vector',
        )

        # Artworks
        fields = Artwork._meta.get_fields()
        for field in fields:
            if field.name not in exclude and hasattr(field, 'verbose_name'):
                ret[field.name] = field.verbose_name

        # the license property is not a field on the Artwork model but part of the serialisation
        ret['license'] = Artwork.get_license_label()
        ret['title_comment'] = Artwork.get_title_comment_label()
        ret['material_description'] = Artwork.get_material_description_label()
        ret['comments'] = Artwork.get_comments_label()

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
    def retrieve_albums(self, request, *args, pk=None, **kwargs):
        """Get all Albums the current user has added this Artwork to."""

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

        albums = Album.objects.filter(
            slides__contains=[{'items': [{'id': artwork.pk}]}],
        ).filter(
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
    def download(self, request, *args, pk=None, **kwargs):
        """Download Artwork image and metadata as a zip file."""

        try:
            artwork = self.get_queryset().get(pk=pk)
        except Artwork.DoesNotExist as dne:
            raise NotFound(_('Artwork does not exist')) from dne

        if artwork.image_original and not artwork.image_fullsize:
            artwork.create_image_fullsize()

        discriminatory_terms = artwork.get_discriminatory_terms_list(
            order_by_length=True,
        )

        def apply_strikethrough(text):
            for term in discriminatory_terms:
                if term in text:
                    strikethrough_term = term[0] + ''.join(
                        [char + '\u0336' for char in term[1:]],
                    )
                    text = text.replace(term, strikethrough_term)
            return text

        # create metadata file content
        metadata_persons = (
            f'{artwork._meta.get_field("artists").verbose_name}: {", ".join([a.name for a in artwork.artists.all()])}\n'
            if artwork.artists.exists()
            else ''
            + f'{artwork._meta.get_field("photographers").verbose_name}: {", ".join([a.name for a in artwork.photographers.all()])}\n'
            if artwork.photographers.exists()
            else ''
            + f'{artwork._meta.get_field("authors").verbose_name}: {", ".join([a.name for a in artwork.authors.all()])}\n'
            if artwork.authors.exists()
            else ''
            + f'{artwork._meta.get_field("graphic_designers").verbose_name}: {", ".join([a.name for a in artwork.graphic_designers.all()])}\n'
            if artwork.graphic_designers.exists()
            else ''
        )

        lang_label = get_language() or settings.LANGUAGE_CODE
        metadata_content = (
            f'{artwork._meta.get_field("title").verbose_name}: {apply_strikethrough(artwork.title)}\n'
            f'{artwork._meta.get_field("title_english").verbose_name}: {apply_strikethrough(artwork.title_english)}\n'
            f'{artwork._meta.get_field("title_comment_"+lang_label).verbose_name}: {apply_strikethrough(artwork.title_comment_localized)}\n'
            f'{metadata_persons}'
            f'{artwork._meta.get_field("date").verbose_name}: {artwork.date}\n'
            f'{artwork._meta.get_field("material_description_"+lang_label).verbose_name}: {artwork.material_description_localized}\n'
            f'{artwork._meta.get_field("dimensions_display").verbose_name}: {artwork.dimensions_display}\n'
            f'{artwork._meta.get_field("comments_"+lang_label).verbose_name}: {apply_strikethrough(artwork.comments_localized)}\n'
            f'{artwork._meta.get_field("credits").verbose_name}: {apply_strikethrough(artwork.credits)}\n'
            f'{artwork._meta.get_field("credits_link").verbose_name}: {artwork.credits_link}\n'
            f'{artwork._meta.get_field("link").verbose_name}: {artwork.link}\n'
            f'{artwork._meta.get_field("keywords").verbose_name}: {", ".join([i.name_localized for i in artwork.keywords.all()])}\n'
            f'{artwork._meta.get_field("location").verbose_name}: {artwork.location.name_localized if artwork.location else ""}\n'
            f'{artwork._meta.get_field("place_of_production").verbose_name}: {", ".join([p.name_localized for p in artwork.place_of_production.all()])}\n'
            '\n\n\n'
            f'{strip_tags(getattr(Text.objects.get(pk=2), get_language(), ""))}'
        )

        output_zip = BytesIO()
        file_name = slugify(artwork.title)

        #  image to zipfile & metadata
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            try:
                zip_file.write(
                    artwork.image_fullsize.path,
                    arcname=f'{file_name}.jpg',
                )
            except FileNotFoundError:
                error_info = (
                    _('File for artwork %(id)s not found') % {'id': artwork.pk},
                )
                logger.exception(error_info)
                return Response(error_info, status.HTTP_500_INTERNAL_SERVER_ERROR)

            zip_file.writestr(f'{file_name}_metadata.txt', metadata_content)

        output_zip.seek(0)

        return FileResponse(
            output_zip,
            as_attachment=True,
            filename=f'{file_name}.zip',
        )
