from django import template

register = template.Library()

# see: url_replace.py

@register.simple_tag
def url_replace(request, field, value):
    d = request.GET.copy()
    d[field] = str(value)
    return d.urlencode()