from base_common_drf.openapi.responses import ERROR_RESPONSES
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.serializers import JSONField

from django.conf import settings
from django.db.models import FloatField, Q, Value
from django.utils.translation import gettext_lazy as _

from api.search.filters import FILTERS, FILTERS_KEYS
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from api.views import check_limit, check_offset
from artworks.models import Artwork, Keyword, Location, PermissionsRelation


def filter_title(filter_values):
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            filters_list.append(
                Q(title__unaccent__icontains=val)
                | Q(title_english__unaccent__icontains=val)
            )
        elif isinstance(val, dict) and 'id' in val.keys():
            filters_list.append(Q(pk=val.get('id')))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for title filter.')
            )

    return filters_list


def filter_artists(filter_values):
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            filters_list.append(Q(artists__name__unaccent__icontains=val))
        elif isinstance(val, dict) and 'id' in val.keys():
            filters_list.append(Q(artists__id=val.get('id')))
        else:
            raise ParseError(
                _('Invalid format of at least one filter_value for artists filter.')
            )

    return filters_list


def filter_albums_for_user(user, owner=True, permissions='EDIT'):
    q_objects = Q()

    if owner:
        q_objects |= Q(user=user)

    permissions = permissions.split(',')

    if permissions:
        q_objects |= Q(
            pk__in=PermissionsRelation.objects.filter(
                user=user,
                permissions__in=permissions,
            ).values_list('album__pk', flat=True)
        )
    return q_objects


def filter_mptt_model(filter_values, model, search_field):
    """Helper function for other filters, to filter a MPTT model based
    field."""
    filters_list = []
    for val in filter_values:
        if isinstance(val, str):
            filters_list.append(
                Q(**{f'{search_field}__name__unaccent__icontains': val})
            )
        elif isinstance(val, dict) and 'id' in val.keys():
            entries = model.objects.filter(pk=val.get('id')).get_descendants(
                include_self=True
            )
            filters_list.append(Q(**{f'{search_field}__in': entries}))
        else:
            raise ParseError(
                f'Invalid format of at least one filter_value for {search_field} filter.'
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
        return [Q(date_year_from__gte=date_from) | Q(date_year_to__gte=date_from)]
    # in case only date_to is provided, all dates past this date should be found
    elif not date_from:
        return [Q(date_year_from__lte=date_to) | Q(date_year_to__lte=date_to)]
    # if both parameters are provided, we search within the given date range
    else:
        return [
            Q(date_year_from__range=[date_from, date_to])
            | Q(date_year_to__range=[date_from, date_to])
            | Q(
                date_year_from__lte=date_from,
                date_year_to__gte=date_to,
            )
        ]


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
        subq = Artwork.objects.search(q_param)
    else:
        subq = Artwork.objects.annotate(rank=Value(1.0, FloatField()))
        if filters:
            subq = subq.order_by('title')
        else:
            # user is not using search at all, therefor show the newest changes first
            subq = subq.order_by('-date_changed', 'title')

    # only search for published artworks
    subq = subq.filter(published=True)

    subq = subq.prefetch_related('artists')

    if exclude:
        subq = subq.exclude(id__in=exclude)

    if filters:
        for f in filters:
            if f['id'] not in FILTERS_KEYS:
                raise ParseError(f'Invalid filter id {repr(f["id"])}')

            filters_list = FILTERS_MAP[f['id']](f['filter_values'])
            for filter_item in filters_list:
                subq = subq.filter(filter_item)

    subq = subq.distinct()

    subq_sql, subq_params = subq.query.sql_with_params()

    qs = Artwork.objects.raw(
        # we need a raw query here, but don't use any unvalidated parameters
        'SELECT *, COUNT(*) OVER() AS "total_count" '  # nosec: see comment above
        f'FROM ({subq_sql}) AS subq '
        'LIMIT %s OFFSET %s;',
        params=(*subq_params, limit, offset),
    )

    total = 0
    results = []

    for artwork in qs:
        # for performance reasons we get the total results count via
        # window function (see raw sql above)
        # and for convenience reasons we just set it in every for loop
        # iteration even though the value is the same for all results
        total = artwork.total_count

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
