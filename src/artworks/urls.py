from django.urls import path

from . import exports, views

urlpatterns = [
    path('', views.artworks_list, name='artworks-list'),
    path('artwork/<int:pk>.json', views.details, name='artwork-details'),
    path(
        'artwork/<int:pk>/detail_overlay/',
        views.artwork_detail_overlay,
        name='artwork_detail_overlay',
    ),
    path('artwork/<int:pk>/edit_overlay/', views.artwork_edit, name='artwork-edit'),
    path('collections/', views.collections_list, name='collections-list'),
    path(
        'collection/<int:pk>_de.pptx',
        exports.collection_download_as_pptx_de,
        name='download-pptx-de',
    ),
    path(
        'collection/<int:pk>_en.pptx',
        exports.collection_download_as_pptx_en,
        name='download-pptx-en',
    ),
    path('collection/<int:pk>.json', views.collection_json, name='collection-json'),
    path('collection/<int:pk>/edit/', views.collection_edit, name='collection-edit'),
    path(
        'collection/<int:pk>/delete/',
        views.collection_delete,
        name='collection-delete',
    ),
    path(
        'artwork-artist-autocomplete/',
        views.ArtworkArtistAutocomplete.as_view(),
        name='artwork-artist-autocomplete',
    ),
    path(
        'artist-autocomplete/',
        views.ArtistAutocomplete.as_view(),
        name='artist-autocomplete',
    ),
    path(
        'artwork-autocomplete/',
        views.ArtworkAutocomplete.as_view(),
        name='artwork-autocomplete',
    ),
    path(
        'keyword-autocomplete/',
        views.KeywordAutocomplete.as_view(),
        name='keyword-autocomplete',
    ),
]
