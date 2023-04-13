from django.urls import re_path

from . import views


urlpatterns = [
    re_path(
        r'^(?P<searchstr>(.*))/$',
        views.autocomplete_search,
        name='lookup',
    ),
]
