from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework import routers

from django.urls import include, path

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('user/', views.UserViewSet.as_view({'get': 'retrieve'}), name='user'),
    # Artworks
    path(
        'artworks/',
        views.ArtworksViewSet.as_view({'get': 'list_artworks'}),
        name='artworks',
    ),
    path(
        'artworks/<item_id>/',
        views.ArtworksViewSet.as_view({'get': 'retrieve_artwork'}),
        name='artwork',
    ),
    path(
        'artworks/<item_id>/albums/',
        views.ArtworksViewSet.as_view({'get': 'retrieve_albums_per_artwork'}),
        name='albums-per-artwork',
    ),
    path(
        'search/',
        views.ArtworksViewSet.as_view({'post': 'search'}),
        name='search_artworks',
    ),
    path(
        'search/filters/',
        views.ArtworksViewSet.as_view({'get': 'list_search_filters'}),
        name='search_filters',
    ),
    path(
        'artworks/<artwork_id>/download/',
        views.ArtworksViewSet.as_view({'get': 'download_artwork'}),
        name='download-artwork',
    ),
    # Folders
    path(
        'folders/',
        views.AlbumViewSet.as_view(
            {
                'get': 'list_folders',
                'post': 'create_folder',
            }
        ),
        name='folders',
    ),
    # Albums
    path(
        'albums/',
        views.AlbumViewSet.as_view(
            {
                'get': 'list_albums',  # per user
                'post': 'create_album',
            }
        ),
        name='albums',
    ),
    path(
        'albums/<album_id>/',
        views.AlbumViewSet.as_view(
            {
                'get': 'retrieve_album',  # retrieve
                'patch': 'update_album',
                'delete': 'delete_album',
            }
        ),
        name='slides',
    ),
    path(
        'albums/<album_id>/slides/',
        views.AlbumViewSet.as_view(
            {'get': 'retrieve_slides_per_album', 'post': 'edit_slides'}
        ),
        name='slides',
    ),
    path(
        'albums/<album_id>/append-artwork/',
        views.AlbumViewSet.as_view({'post': 'append_artwork'}),
        name='append_artwork',
    ),
    path(
        'albums/<album_id>/permissions/',
        views.AlbumViewSet.as_view(
            {
                'get': 'retrieve_permissions_per_album',
                'post': 'create_permissions',
                'delete': 'delete_permissions',
            }
        ),
        name='permissions',
    ),
    path(
        'albums/<album_id>/download/',
        views.AlbumViewSet.as_view({'get': 'download_album'}),
        name='download-album',
    ),
    # Labels
    path('labels/', views.LabelsViewSet.as_view({'get': 'list_labels'}), name='labels'),
    path('autocomplete/', include('autocomplete.urls')),
    path('openapi.yaml', SpectacularAPIView.as_view(), name='schema_yaml'),
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema_json'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema_json'),
        name='schema_docs',
    ),
]
