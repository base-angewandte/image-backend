from django.urls import include, re_path

from . import urls_autocomplete

urlpatterns = [
    re_path('', include(urls_autocomplete)),
]
