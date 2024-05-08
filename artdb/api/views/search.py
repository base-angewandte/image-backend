from api.search.filters import FILTERS, FILTERS_KEYS
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from api.views import check_limit, check_offset
from artworks.models import Artwork, Keyword, Location
from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.serializers import JSONField

from django.conf import settings
from django.db.models import Count, FloatField, Q, Value, Window
from django.utils.translation import gettext_lazy as _


def filter_title(filter_values):
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(title__unaccent__icontains=val) | Q(
                title_english__unaccent__icontains=val
            )
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects &= Q(pk=val.get('id'))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for title filter.')
            )

    return q_objects


def filter_artists(filter_values):
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(artists__name__unaccent__icontains=val)
        elif isinstance(val, dict) and 'id' in val.keys():
            q_objects &= Q(artists__id=val.get('id'))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for artists filter.')
            )

    return q_objects


def filter_mptt_model(filter_values, model, search_field):
    """Helper function for other filters, to filter a MPTT model based
    field."""
    q_objects = Q()
    for val in filter_values:
        if isinstance(val, str):
            q_objects &= Q(**{f'{search_field}__name__unaccent__icontains': val})
        elif isinstance(val, dict) and 'id' in val.keys():
            entries = model.objects.filter(pk=val.get('id')).get_descendants(
                include_self=True
            )
            q_objects &= Q(**{f'{search_field}__in': entries})
        else:
            raise ParseError(
                f'Invalid format of at least one filter_value for {search_field} filter.'
            )

    return q_objects


def filter_place_of_production(filter_values):
    return filter_mptt_model(filter_values, Location, 'place_of_production')


def filter_location(filter_values):
    return filter_mptt_model(filter_values, Location, 'location')


def filter_keywords(filter_values):
    return filter_mptt_model(filter_values, Keyword, 'keywords')


def filter_date(filter_values):
    if not isinstance(filter_values, dict) or (
        'date_from' not in filter_values and 'date_to' not in filter_values
    ):
        raise ParseError(_('Invalid filter_value format for date filter.'))

    date_from = filter_values.get('date_from')
    date_to = filter_values.get('date_to')
    if not date_from and not date_to:
        raise ParseError(_('Invalid filter_value format for date filter.'))
    try:
        if date_from:
            date_from = int(date_from)
        if date_to:
            date_to = int(date_to)
    except ValueError as err:
        raise ParseError(
            _('Invalid format of at least one filter_value for date filter.')
        ) from err

    if date_from and date_to and date_to < date_from:
        raise ParseError(_('date_from needs to be less than or equal to date_to.'))

    # in case only date_from is provided, all dates in its future should be found
    if not date_to:
        return Q(date_year_from__gte=date_from) | Q(date_year_to__gte=date_from)
    # in case only date_to is provided, all dates past this date should be found
    elif not date_from:
        return Q(date_year_from__lte=date_to) | Q(date_year_to__lte=date_to)
    # if both parameters are provided, we search within the given date range
    else:
        return (
            Q(date_year_from__range=[date_from, date_to])
            | Q(date_year_to__range=[date_from, date_to])
            | Q(
                date_year_from__lte=date_from,
                date_year_to__gte=date_to,
            )
        )


FILTERS_MAP = {}
for filter_id in FILTERS_KEYS:
    FILTERS_MAP[filter_id] = globals()[f'filter_{filter_id}']


@extend_schema(
    tags=['search'],
    request=SearchRequestSerializer,
    examples=[
        OpenApiExample(
            name='search with filter type title, artist, place_of_production, current_location, keywords',
            value={
                'limit': settings.SEARCH_LIMIT,
                'offset': 0,
                'exclude': [123, 345],  # with artwork ids
                'q': 'query string',  # the string from general search
                'filters': [
                    {
                        'id': 'artists',
                        'filter_values': ['lassnig', {'id': 1192}],
                    }
                ],
            },
        ),
        OpenApiExample(
            name='search with filter type date',
            value={
                'limit': settings.SEARCH_LIMIT,
                'offset': 0,
                'exclude': [123, 345],  # with artwork ids
                'q': 'query string',  # the string from general search
                'filters': [
                    {
                        'id': 'date',
                        'filter_values': {
                            'date_from': '2000',
                            'date_to': '2001',
                        },
                    }
                ],
            },
        ),
    ],
    responses={
        200: SearchResultSerializer,
        403: ERROR_RESPONSES[403],
        404: ERROR_RESPONSES[404],
    },
)
@api_view(['post'])
def search(request, *args, **kwargs):
    serializer = SearchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    limit = check_limit(serializer.validated_data.get('limit'))
    offset = check_offset(serializer.validated_data.get('offset'))
    filters = serializer.validated_data.get('filters', [])
    q_param = serializer.validated_data.get('q')
    exclude = serializer.validated_data.get('exclude', [])

    if q_param:
        qs = Artwork.objects.search(q_param).annotate(total_results=Window(Count('pk')))
    else:
        qs = Artwork.objects.annotate(rank=Value(1.0, FloatField())).annotate(
            total_results=Window(Count('pk'))
        )
        if filters:
            qs = qs.order_by('title')
        else:
            # user is not using search at all, therefor show the newest changes first
            qs = qs.order_by('-updated_at', 'title')

    # only search for published artworks
    qs = qs.filter(published=True)

    qs = qs.prefetch_related('artists')

    if exclude:
        qs = qs.exclude(id__in=exclude)

    if filters:
        q_objects = Q()

        for f in filters:
            if f['id'] not in FILTERS_KEYS:
                raise ParseError(f'Invalid filter id {repr(f["id"])}')

            q_objects &= FILTERS_MAP[f['id']](f['filter_values'])

        qs = qs.filter(q_objects).distinct()

    qs = qs[offset : offset + limit]

    total = 0
    results = []

    for artwork in qs:
        # for performance reasons we get the total results count via annotation
        # annotate(total_results=Window(Count('pk')))
        # and for convenience reasons we just set it in every for loop
        # iteration even though the value is the same for all results
        total = artwork.total_results

        results.append(
            {
                'id': artwork.id,
                'image_original': request.build_absolute_uri(artwork.image_original.url)
                if artwork.image_original
                else None,
                'credits': artwork.credits,
                'title': artwork.title,
                'date': artwork.date,
                'artists': [
                    {'value': artist.name, 'id': artist.id}
                    for artist in artwork.artists.all()
                ],
                'score': artwork.rank,
            }
        )

    return Response({'total': total, 'results': results})


@extend_schema(
    tags=['search'],
    responses={
        200: inline_serializer(
            name='SearchFiltersResponse',
            fields={k: JSONField() for k in FILTERS_KEYS},
        ),
        403: ERROR_RESPONSES[403],
        404: ERROR_RESPONSES[404],
    },
)
@api_view(['get'])
def search_filters(request, *args, **kwargs):
    return Response(FILTERS)
