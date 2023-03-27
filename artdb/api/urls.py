from django.urls import include, re_path

from . import urls_api

urlpatterns = [
    re_path(r'v1/', include(urls_api))
]
