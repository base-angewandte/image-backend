from django.urls import path, re_path
from artworks.views import *

urlpatterns = [
    path('', index, name='artworks_list'),
    path('artwork/<int:id>.json', details, name='artwork_details'),
    path('artwork/<int:id>_detail_overlay.html', artwork_detail_overlay, name='artwork_detail_overlay'),
    path('artwork/<int:id>.html', artwork, name='artwork'),    
    path('artwork_new.html', artwork_new, name='artwork_new'),
    path('artwork/edit/<int:id>.html', artwork_edit, name='artwork_edit'),
    path('artwork/delete/<int:id>.html', artwork_delete, name='artwork_delete'),
    path('collection/<int:id>', collection, name='artwork_collection'),
    path('collection/<int:collection_id>/remove/<int:artwork_id>', collection_remove_artwork, name='artwork_collection'),
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