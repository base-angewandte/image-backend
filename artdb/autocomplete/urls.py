from django.urls import include, re_path

from . import urls_autosuggest

urlpatterns = [
    re_path('', include(urls_autosuggest)),
]
