from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from django.urls import include, path

from .views.albums import AlbumsViewSet
from .views.artworks import ArtworksViewSet
from .views.folders import FoldersViewSet
from .views.permissions import PermissionsViewSet
from .views.search import SearchViewSet
from .views.tos import TosViewSet
from .views.user import UserViewSet

router = routers.DefaultRouter()

router.register('artworks', ArtworksViewSet, basename='artwork')
router.register('albums', AlbumsViewSet, basename='album')
router.register('permissions', PermissionsViewSet, basename='permission')
router.register('folders', FoldersViewSet, basename='folder')
router.register('search', SearchViewSet, basename='search')
router.register('tos', TosViewSet, basename='tos')
router.register('user', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # Autocomplete
    path('autocomplete/', include('api.autocomplete.urls')),
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
