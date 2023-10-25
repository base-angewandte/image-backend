from django.urls import include, path

from . import urls_autocomplete

urlpatterns = [
    path('', include(urls_autocomplete)),
]
