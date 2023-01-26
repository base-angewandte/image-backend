from django.conf import settings
from django.urls import re_path

from . import views

# NOTE: fieldname must be present in ACTIVE_SOURCES for this to work
urlpatterns = [
    re_path(
        r'^(?P<fieldname>({}))/$'.format('|'.join(settings.ACTIVE_SOURCES.keys())),
        views.lookup_view,
        name='lookup_all',
    ),
    re_path(
        r'^(?P<fieldname>({}))/(?P<searchstr>(.*))/$'.format(
            '|'.join(settings.ACTIVE_SOURCES.keys())
        ),
        views.lookup_view_search,
        name='lookup',
    ),
    # Autosuggest for users
    re_path(
        r'^(?P<user>(.*))/$',
        views.autosuggest_user,
        name='autosuggest_user',
    ),
]
