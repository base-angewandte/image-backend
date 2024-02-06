import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='json')
def json_dumps(value):
    return mark_safe(json.dumps(value))  # nosec B308, B703


@register.filter
def permissions_to_json(value):
    value = value if value else []
    if isinstance(value, str):
        value = value.split(',')
    return mark_safe(json.dumps(value))  # nosec B308, B703
