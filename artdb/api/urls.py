from django.urls import include, path

from . import urls_api

urlpatterns = [
    path('v1/', include(urls_api)),
]
