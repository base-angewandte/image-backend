from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _


def autocomplete_url(type_id):
    return f'{reverse("autocomplete", kwargs={"version":"v1"})}?type={type_id}'


autocomplete_url_lazy = lazy(autocomplete_url, str)


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
            'placeholder': f'{_("Enter")} {FILTER_LABELS["title"]}',
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
            'placeholder': f'{_("Enter")} {FILTER_LABELS["artist"]}',
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
            'placeholder': f'{_("Enter")} {FILTER_LABELS["place_of_production"]}',
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
            'placeholder': f'{_("Enter")} {FILTER_LABELS["location"]}',
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
            'placeholder': f'{_("Enter")} {FILTER_LABELS["keywords"]}',
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
            'placeholder': {'date': f'{_("Enter")} {_("Date")}'},
            'order': 6,
        },
    },
}

FILTERS_KEYS = FILTERS.keys()
