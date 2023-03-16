from django.urls import include, re_path

from . import urls_autocomplete

urlpatterns = [
    re_path('', include(urls_autocomplete)),
    # re_path(r'^(?P<version>(v1))/', include(urls_api)),
]
