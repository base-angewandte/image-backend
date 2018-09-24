from django.urls import path, re_path
from artworks.views import *

urlpatterns = [
    path('', index, name='artworks_list'),
    path('artwork/<int:id>.json', details, name='artwork_details'),
    path('artwork/<int:id>/detail_overlay.html', artwork_detail_overlay, name='artwork_detail_overlay'),
    path('artwork/<int:id>.html', artwork, name='artwork'),    
    path('artwork_new.html', artwork_new, name='artwork_new'),
    path('artwork/<int:id>/edit_overlay.html', artwork_edit, name='artwork_edit'),
    path('artwork/<int:id>/delete_overlay.html', artwork_delete, name='artwork_delete'),
    path('artwork/<int:id>/collect_overlay.html', artwork_collect, name='artwork_collect'),
    path('collection/<int:id>', collection_list, name='collection'),
    path('collections.html', collections_list, name='collections_list'),
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
    path('artist/<int:id>.html', artist_artworks, name='artist_artworks'),
]