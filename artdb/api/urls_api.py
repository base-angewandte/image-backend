from rest_framework import routers

from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView, SpectacularJSONAPIView


from . import views

router = routers.DefaultRouter()

urlpatterns = [
    re_path('', include(router.urls)),
    path('user/', views.UserViewSet.as_view({'get': 'retrieve'}), name='user'), # todo ?

    # Artworks
    path('artworks/', views.ArtworksViewSet.as_view({
        'get': 'list',}), name='artworks'),
        # 'post': 'search_artworks'}), name='artworks'),  # todo update
    path('artworks/<item_id>/', views.ArtworksViewSet.as_view({'get': 'retrieve'}), name='artwork'),
    path('artworks-search/', views.ArtworksViewSet.as_view({
        'get': 'search_artworks'}), name='search_artworks'),

    # ArtworkCollections
    ## todo Folders are renamed to Albums?
    path('folders/', views.AlbumViewSet.as_view({
        'get': 'list_folders',
        'post': 'create_folder',  # todo or         Create Folder /albums/{id}?
    }), name='folders'),
    path('albums/', views.AlbumViewSet.as_view({
        'get': 'list_albums', # per user
    }), name='albums'),
    path('albums/<album_id>/', views.AlbumViewSet.as_view({
            'get': 'retrieve_album',  # retrieve
            'patch': 'update_album',
            'delete': 'delete_album',
        }), name='slides'),

    path('albums/<album_id>/slides/', views.AlbumViewSet.as_view({
            'get': 'retrieve_slides_per_album',
            'post': 'edit_slides'}), name='slides'),

    # As it was: separate endpoints
    #
    # path('albums/<album_id>/slides/reorder_artworks', views.ArtworksCollectionViewSet.as_view({
    #         'put': 'reorder_artworks_within_slide'}), name='reorder_artworks_in_slides'),
    #
    # path('albums/<album_id>/slides/separate_slides', views.ArtworksCollectionViewSet.as_view({
    #     'put': 'separate_slides',}), name='separate_slides'),
    #
    # path('albums/<album_id>/slides/reorder_slides', views.ArtworksCollectionViewSet.as_view({
    #     'put': 'reorder_slides'}), name='reorder_slides'),

###############

    path('autocomplete/', include('autocomplete.urls')),
    path('schema/openapi3.yaml', SpectacularAPIView.as_view(), name='schema'),
    path('schema/openapi3.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path('schema/swagger-ui',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
