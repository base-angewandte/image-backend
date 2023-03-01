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
        'get': 'list'}), name='artworks'),
    path('artworks/<item_id>/', views.ArtworksViewSet.as_view({'get': 'retrieve'}), name='artwork'),

    # ArtworkCollections
    ## todo Folders are renamed to Albums?
    path('folders/', views.ArtworksCollectionViewSet.as_view({
        'get': 'list_folders',
        'post': 'create_folder',  # todo or         Create Folder /workbooks/{id}?
    }), name='folders'),
    path('workbooks/', views.ArtworksCollectionViewSet.as_view({
        'get': 'list_workbooks', # per user
    }), name='workbooks'),
    path('workbooks/<workbook_id>/', views.ArtworksCollectionViewSet.as_view({
            'get': 'retrieve_workbook',  # retrieve
            'patch': 'update_workbook',
            'delete': 'delete_workbook',
        }), name='slides'),

    path('workbooks/<workbook_id>/slides/', views.ArtworksCollectionViewSet.as_view({
            'get': 'retrieve_slides_per_workbook',
            'post': 'edit_slides'}), name='slides'),

    # As it was: separate endpoints
    #
    # path('workbooks/<workbook_id>/slides/reorder_artworks', views.ArtworksCollectionViewSet.as_view({
    #         'put': 'reorder_artworks_within_slide'}), name='reorder_artworks_in_slides'),
    #
    # path('workbooks/<workbook_id>/slides/separate_slides', views.ArtworksCollectionViewSet.as_view({
    #     'put': 'separate_slides',}), name='separate_slides'),
    #
    # path('workbooks/<workbook_id>/slides/reorder_slides', views.ArtworksCollectionViewSet.as_view({
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
