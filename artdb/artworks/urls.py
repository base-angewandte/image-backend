from django.urls import path, re_path
from artworks.views import *

urlpatterns = [
    path('', artworks_list, name='artworks-list'),
    path('artwork/<int:id>.json', details, name='artwork-details'),
    path('artwork/<int:id>/detail_overlay/', artwork_detail_overlay, name='artwork_detail_overlay'), 
    path('artwork/<int:id>/edit_overlay/', artwork_edit, name='artwork-edit'),
    path('artwork/<int:id>/collect_overlay/', artwork_collect, name='artwork-collect'),
    path('collections/', collections_list, name='collections-list'),
    path('collection/<int:id>/', collection, name='collection'),
    path('collection/<int:id>_de.pptx', collection_download_as_pptx_de, name="download-pptx-de"),
    path('collection/<int:id>_en.pptx', collection_download_as_pptx_en, name="download-pptx-en"),
    path('collection/<int:id>.json', collection_json, name='collection-json'),
    path('collection/<int:id>/edit/', collection_edit, name='collection-edit'),
    path('collection/<int:id>/delete/', collection_delete, name='collection-delete'),
    re_path(
        r'^artist-autocomplete/$',
        ArtistAutocomplete.as_view(),
        name='artist-autocomplete',
    ),
        re_path(
        r'^artwork-autocomplete/$',
        ArtworkAutocomplete.as_view(),
        name='artwork-autocomplete',
    ),
        re_path(
        r'^keyword-autocomplete/$',
        KeywordAutocomplete.as_view(),
        name='keyword-autocomplete',
    ),
]