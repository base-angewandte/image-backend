from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from django.urls import include, path

from .autocomplete import urls as autocomplete_urls
from .views.albums import AlbumsViewSet
from .views.artworks import ArtworksViewSet
from .views.folders import FoldersViewSet
from .views.permissions import PermissionsViewSet
from .views.search import search, search_filters
from .views.tos import TosViewSet
from .views.user import get_user_data

router = routers.DefaultRouter()

router.register('artworks', ArtworksViewSet, basename='artwork')
router.register('albums', AlbumsViewSet, basename='album')
router.register('permissions', PermissionsViewSet, basename='permission')
router.register('folders', FoldersViewSet, basename='folder')
router.register('tos', TosViewSet, basename='tos')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', get_user_data, name='user'),
    # Search
    path('search/', search, name='search'),
    path('search/filters/', search_filters, name='search-filters'),
    # Autocomplete
    path('autocomplete/', include(autocomplete_urls)),
    # Schema
    path('openapi.yaml', SpectacularAPIView.as_view(), name='schema-yaml'),
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema-json'),
    # Schema Docs / Swagger UI
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema-json'),
        name='schema-docs',
    ),
]
