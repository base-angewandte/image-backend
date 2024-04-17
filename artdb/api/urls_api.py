from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from django.urls import include, path

from . import views
from .autocomplete import urls as autocomplete_urls

router = routers.DefaultRouter()

router.register('artworks', views.ArtworksViewSet, basename='artwork')
router.register('albums', views.AlbumsViewSet, basename='album')
router.register('labels', views.LabelsViewSet, basename='label')
router.register('permissions', views.PermissionsViewSet, basename='permission')
router.register('folders', views.FoldersViewSet, basename='folder')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', views.get_user_data, name='user'),
    # Search
    path('search/', views.search, name='search'),
    path('search/filters/', views.search_filters, name='search-filters'),
    # Autocomplete
    path('autocomplete/', include(autocomplete_urls)),
    # Schema
    path('openapi.yaml', SpectacularAPIView.as_view(), name='schema_yaml'),
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema_json'),
    # Schema Docs / Swagger UI
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema_json'),
        name='schema_docs',
    ),
]
