from django.conf import settings
from django.urls import re_path

from . import views

## DUMMY
# TODO complete

# SOURCES = {
#     # 'contributors': CONTRIBUTORS,  # GND, VIAF
#     'expertise': {
#         'search': 'core.skosmos.get_skills',
#     },
# 'artworks': {
#         'search': 'core.skosmos.get_skills',
#     },
#     'workbooks': {
#         'search': 'core.skosmos.get_skills',
#     }
# }

# Dummy below


# NOTE: fieldname must be present in ACTIVE_SOURCES for this to work
from .views import SOURCES

urlpatterns = [
    re_path(
        # r'^(?P<type>({}))/(?P<searchstr>(.*))/$'.format(
        #     '|'.join(SOURCES)
        # ),
        r'^(?P<type_param>(.*))/(?P<searchstr>(.*))/$',
        views.autocomplete_search,
        name='lookup',
    ),
]
