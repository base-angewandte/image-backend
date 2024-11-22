import operator
from functools import reduce

from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.serializers import JSONField

from django.conf import settings
from django.db.models import FloatField, Q, Value
from django.utils.translation import gettext_lazy as _

from artworks.models import Artwork, Keyword, Location

from ..search.filters import FILTERS, FILTERS_KEYS
from ..serializers.search import SearchRequestSerializer, SearchResultSerializer
from . import check_limit, check_offset


def filter_title(filter_values):
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            filters_list.append(
                Q(title__unaccent__icontains=val)
                | Q(title_english__unaccent__icontains=val),
            )
        elif isinstance(val, dict) and 'id' in val:
            filters_list.append(Q(pk=val.get('id')))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for title filter.'),
            )

    return filters_list


def filter_artists(filter_values):
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            filters_list.append(
                Q(artists__name__unaccent__icontains=val)
                | Q(authors__name__unaccent__icontains=val)
                | Q(photographers__name__unaccent__icontains=val)
                | Q(graphic_designers__name__unaccent__icontains=val)
                | Q(artists__synonyms__icontains=val)
                | Q(authors__synonyms__icontains=val)
                | Q(photographers__synonyms__icontains=val)
                | Q(graphic_designers__synonyms__icontains=val),
            )
        elif isinstance(val, dict) and 'id' in val:
            filters_list.append(
                Q(artists__id=val.get('id'))
                | Q(authors__id=val.get('id'))
                | Q(photographers__id=val.get('id'))
                | Q(graphic_designers__id=val.get('id')),
            )
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for artists filter.'),
            )

    return filters_list


def filter_mptt_model(filter_values, model, search_field):
    """Helper function for other filters, to filter a MPTT model based
    field."""
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            q_filters = [
                {f'{search_field}__name__unaccent__icontains': val},
                {f'{search_field}__name_en__unaccent__icontains': val},
            ]

            if search_field in ('place_of_production', 'location'):
                q_filters.append(
                    {f'{search_field}__synonyms__icontains': val},
                )

            filters_list.append(
                reduce(operator.or_, (Q(**x) for x in q_filters)),
            )
        elif isinstance(val, dict) and 'id' in val:
            entries = model.objects.filter(pk=val.get('id')).get_descendants(
                include_self=True,
            )
            filters_list.append(Q(**{f'{search_field}__in': entries}))
        else:
            raise ParseError(
                f'Invalid format of at least one filter_value for {search_field} filter.',
            )
    return filters_list


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

    # ensure at least one parameter is provided
    if not date_from and not date_to:
        raise ParseError(_('Invalid filter_value format for date filter.'))

    # check if provided parameters are integers
    try:
        date_from = int(date_from) if date_from else None
        date_to = int(date_to) if date_to else None
    except ValueError as err:
        raise ParseError(
            _('Invalid format of at least one filter_value for date filter.'),
        ) from err

    # if both parameters are provided, check that date_from <= date_to
    if date_from is not None and date_to is not None and date_to < date_from:
        raise ParseError(_('date_from needs to be less than or equal to date_to.'))

    # in case only date_from is provided, all dates in its future should be found
    if date_to is None:
        return [Q(date_year_from__gte=date_from) | Q(date_year_to__gte=date_from)]
    # in case only date_to is provided, all dates past this date should be found
    elif date_from is None:
        return [Q(date_year_from__lte=date_to) | Q(date_year_to__lte=date_to)]
    # if both parameters are provided, we search within the given date range
    else:
        return [
            Q(date_year_from__range=[date_from, date_to])
            | Q(date_year_to__range=[date_from, date_to])
            | Q(
                date_year_from__lte=date_from,
                date_year_to__gte=date_to,
            ),
        ]


# maps filter_id to corresponding filter_* function defined above
FILTERS_MAP = {}
for filter_id in FILTERS_KEYS:
    FILTERS_MAP[filter_id] = globals()[f'filter_{filter_id}']


@extend_schema(tags=['search'])
class SearchViewSet(viewsets.GenericViewSet):
    @extend_schema(
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
                        },
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
                        },
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
    def create(self, request, *args, **kwargs):
        """Search for Artworks."""

        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        limit = check_limit(serializer.validated_data.get('limit'))
        offset = check_offset(serializer.validated_data.get('offset'))
        filters = serializer.validated_data.get('filters', [])
        q_param = serializer.validated_data.get('q')
        exclude = serializer.validated_data.get('exclude', [])

        if q_param:
            subq = Artwork.objects.search(q_param)
            order_by = '"rank" DESC, "similarity_title" DESC, "similarity_title_english" DESC, "similarity_persons" DESC, "date_changed" DESC'
        else:
            subq = Artwork.objects.annotate(rank=Value(1.0, FloatField()))
            # if user is using search, sort by title, else show the newest changes first
            order_by = (
                '"title", "date_changed" DESC'
                if filters
                else '"date_changed" DESC, "title"'
            )

        # only search for published artworks
        subq = subq.filter(published=True)

        if exclude:
            subq = subq.exclude(id__in=exclude)

        if filters:
            for f in filters:
                if f['id'] not in FILTERS_KEYS:
                    raise ParseError(f'Invalid filter id {repr(f["id"])}')
                filters_list = FILTERS_MAP[f['id']](f['filter_values'])
                for filter_item in filters_list:
                    subq = subq.filter(filter_item)

        # we need to remove the previously set ordering to be able to use
        # distinct only on id field
        subq = subq.order_by().distinct('id')

        subq_sql, subq_params = subq.query.sql_with_params()

        qs = Artwork.objects.raw(
            # we need a raw query here, but don't use any unvalidated parameters
            'SELECT *, COUNT(*) OVER() AS "total_count" '  # noqa: S608, see comment above
            f'FROM ({subq_sql}) AS subq '
            f'ORDER BY {order_by} '
            'LIMIT %s OFFSET %s',
            params=(*subq_params, limit, offset),
        ).prefetch_related(
            'artists',
            'photographers',
            'authors',
            'graphic_designers',
            'discriminatory_terms',
        )

        total = 0
        results = []

        for artwork in qs:
            # for performance reasons we get the total results count via
            # window function (see raw sql above)
            # and for convenience reasons we just set it in every for loop
            # iteration even though the value is the same for all results
            total = artwork.total_count

            artwork_serialized = {
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
                'discriminatory_terms': [
                    # we iterate over discriminatory_terms directly instead of using
                    # artwork.get_discriminatory_terms_list() to ensure that we are
                    # using the results already fetched with prefetch_related()
                    dt.term
                    for dt in artwork.discriminatory_terms.all()
                ],
                'date': artwork.date,
                'artists': [
                    {'value': artist.name, 'id': artist.id}
                    for artist in artwork.artists.all()
                ],
                'score': artwork.rank,
            }
            if request.user.is_editor:
                artwork_serialized['editing_link'] = artwork.editing_link
            results.append(artwork_serialized)

        return Response({'total': total, 'results': results})

    @extend_schema(
        responses={
            200: inline_serializer(
                name='SearchFiltersResponse',
                fields={k: JSONField() for k in FILTERS_KEYS},
            ),
            403: ERROR_RESPONSES[403],
            404: ERROR_RESPONSES[404],
        },
    )
    @action(detail=False, methods=['GET'])
    def filters(self, request, *args, **kwargs):
        """Get available search filters."""

        return Response(FILTERS)
