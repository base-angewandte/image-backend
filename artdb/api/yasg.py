from drf_yasg import openapi

from django.conf import settings

language_header_parameter = openapi.Parameter(
    'Accept-Language',
    openapi.IN_HEADER,
    required=False,
    type=openapi.TYPE_STRING,
    enum=list(settings.LANGUAGES_DICT.keys()),
)
