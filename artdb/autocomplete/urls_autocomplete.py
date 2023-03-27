from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r'^(?P<type_param>(.*))/(?P<searchstr>(.*))/$',
        views.autocomplete_search,
        name='lookup',
    ),
]
