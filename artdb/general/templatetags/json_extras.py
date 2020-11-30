from django import template
from django.utils.safestring import mark_safe

import json

register = template.Library()


@register.filter(name='json')
def json_dumps(value):
    return mark_safe(json.dumps(value))


@register.filter
def permissions_to_json(value):
    value = value if value else []
    if isinstance(value, str):
        value = value.split(',')
    return mark_safe(json.dumps(value))
