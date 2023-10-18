from django.urls import path, re_path
from . import views, exports

urlpatterns = [
    path('', views.artworks_list, name='artworks-list'),
    path('artwork/<int:id>.json', views.details, name='artwork-details'),
    path('artwork/<int:id>/detail_overlay/', views.artwork_detail_overlay, name='artwork_detail_overlay'),
    path('artwork/<int:id>/edit_overlay/', views.artwork_edit, name='artwork-edit'),
    path('artwork/<int:id>/collect_overlay/', views.artwork_collect, name='artwork-collect'),
    path('collections/', views.collections_list, name='collections-list'),
    path('collection/<int:id>/', views.collection, name='collection'),
    path('collection/<int:id>_de.pptx', exports.collection_download_as_pptx_de, name="download-pptx-de"),
    path('collection/<int:id>_en.pptx', exports.collection_download_as_pptx_en, name="download-pptx-en"),
    path('collection/<int:id>.json', views.collection_json, name='collection-json'),
    path('collection/<int:id>/edit/', views.collection_edit, name='collection-edit'),
    path('collection/<int:id>/delete/', views.collection_delete, name='collection-delete'),

    path('artwork-artist-autocomplete/', views.ArtworkArtistAutocomplete.as_view(), name='artwork-artist-autocomplete'),

    path('artist-autocomplete/', views.ArtistAutocomplete.as_view(), name='artist-autocomplete'),
    path('artwork-autocomplete/', views.ArtworkAutocomplete.as_view(), name='artwork-autocomplete'),
    path('keyword-autocomplete/', views.KeywordAutocomplete.as_view(), name='keyword-autocomplete'),
]
