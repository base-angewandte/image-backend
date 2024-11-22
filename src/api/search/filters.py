from django.db.models import Q
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

from artworks.models import PermissionsRelation


def autocomplete_url(type_id):
    return f'{reverse("autocomplete", kwargs={"version":"v1"})}?type={type_id}'


autocomplete_url_lazy = lazy(autocomplete_url, str)

placeholder_lazy = lazy(lambda label: _('Enter %(label)s') % {'label': label}, str)

FILTER_LABELS = {
    'title': _('Title'),
    'artist': _('Artist'),
    'place_of_production': _('Place of Production'),
    'location': _('Location'),
    'keywords': _('Keywords'),
    'date': _('Date from, to'),
}

FILTERS = {
    'title': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'label': {'type': 'string'},
            },
        },
        'title': FILTER_LABELS['title'],
        'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'dynamic_autosuggest': True,
            'allow_unknown_entries': True,
            'source': autocomplete_url_lazy('titles'),
            'placeholder': placeholder_lazy(FILTER_LABELS['title']),
            'order': 1,
        },
    },
    'artists': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'label': {'type': 'string'},
            },
        },
        'title': FILTER_LABELS['artist'],
        'x-attrs': {
            'field_format': 'half',
            'field_type': 'chips',
            'dynamic_autosuggest': True,
            'allow_unknown_entries': True,
            'source': autocomplete_url_lazy('artists'),
            'placeholder': placeholder_lazy(FILTER_LABELS['artist']),
            'order': 2,
        },
    },
    'place_of_production': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'label': {'type': 'string'},
            },
        },
        'title': FILTER_LABELS['place_of_production'],
        'x-attrs': {
            'field_format': 'third',
            'field_type': 'chips',
            'dynamic_autosuggest': True,
            'allow_unknown_entries': True,
            'source': autocomplete_url_lazy('locations'),
            'placeholder': placeholder_lazy(FILTER_LABELS['place_of_production']),
            'order': 3,
        },
    },
    'location': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'label': {'type': 'string'},
            },
        },
        'title': FILTER_LABELS['location'],
        'x-attrs': {
            'field_format': 'third',
            'field_type': 'chips',
            'dynamic_autosuggest': True,
            'allow_unknown_entries': True,
            'source': autocomplete_url_lazy('locations'),
            'placeholder': placeholder_lazy(FILTER_LABELS['location']),
            'order': 4,
        },
    },
    'keywords': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'label': {'type': 'string'},
            },
        },
        'title': FILTER_LABELS['keywords'],
        'x-attrs': {
            'placeholder': placeholder_lazy(FILTER_LABELS['keywords']),
            'order': 5,
            'field_format': 'third',
            'field_type': 'chips',
            'allow_unknown_entries': False,
            'dynamic_autosuggest': True,
            'source': autocomplete_url_lazy('keywords'),
        },
    },
    'date': {
        'type': 'object',
        'properties': {
            'date_from': {'type': 'string'},
            'date_to': {'type': 'string'},
        },
        'title': FILTER_LABELS['date'],
        'additionalProperties': False,
        'x-attrs': {
            'field_format': 'full',
            'field_type': 'date',
            'date_format': 'year',
            'placeholder': {'date': placeholder_lazy(_('Year'))},
            'order': 6,
        },
    },
}

FILTERS_KEYS = FILTERS.keys()


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
            ).values_list('album__pk', flat=True),
        )
    return q_objects
