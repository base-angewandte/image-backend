import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def csv_to_json(value, arg=','):
    value = value.split(arg) if value else []
    return mark_safe(json.dumps(value))
