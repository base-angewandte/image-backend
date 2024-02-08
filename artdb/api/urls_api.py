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

urlpatterns = [
    path('', include(router.urls)),
    path('user/', views.get_user_data, name='user'),
    # Search
    path('search/', views.search, name='search'),
    path('search/filters/', views.search_filters, name='search-filters'),
    # Artworks
    path(
        'artworks/<id>/albums/',
        views.ArtworksViewSet.as_view({'get': 'retrieve_albums'}),
        name='artwork-albums',
    ),
    path(
        'artworks/<id>/download/',
        views.ArtworksViewSet.as_view({'get': 'download'}),
        name='artwork-download',
    ),
    # Folders
    path(
        'folders/',
        views.AlbumsViewSet.as_view(
            {
                'get': 'list_folders',
                'post': 'create_folder',
            }
        ),
        name='folders',
    ),
    # Albums
    path(
        'albums/<id>/slides/',
        views.AlbumsViewSet.as_view(
            {
                'get': 'retrieve_slides',
                'post': 'create_slides',
            }
        ),
        name='album-slides',
    ),
    path(
        'albums/<id>/append-artwork/',
        views.AlbumsViewSet.as_view({'post': 'append_artwork'}),
        name='album-append-artwork',
    ),
    path(
        'albums/<id>/permissions/',
        views.AlbumsViewSet.as_view(
            {
                'get': 'retrieve_permissions',
                'post': 'create_permissions',
                'delete': 'destroy_permissions',
            }
        ),
        name='album-permissions',
    ),
    path(
        'albums/<id>/download/',
        views.AlbumsViewSet.as_view({'get': 'download'}),
        name='album-download',
    ),
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
