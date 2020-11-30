import json
import logging

from django import template
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

register = template.Library()


@register.filter
def csv_to_json(value, arg=','):
    value = value.split(arg) if value else []
    return mark_safe(json.dumps(value))
