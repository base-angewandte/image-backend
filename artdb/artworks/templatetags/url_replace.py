from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """
    Used by proper_paginate.py and templates/artwork/artwork_pagination.html
    """
    d = request.GET.copy()
    d[field] = str(value)
    return d.urlencode()