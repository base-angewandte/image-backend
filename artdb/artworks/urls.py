from django.urls import path, re_path
from artworks.views import *

urlpatterns = [
    path('', index, name='artworks_list'),
    path('artwork/<int:id>.json', details, name='artwork_details'),
    path('artwork/<int:id>_overlay.html', artwork_overlay_only, name='artwork_overlay_only'),
    path('artwork/<int:id>.html', artwork, name='artwork'),    
    path('artwork_new.html', artwork_new, name='artwork_new'),
    path('artwork/edit/<int:id>.html', artwork_edit, name='artwork_edit'),
    path('artwork/delete/<int:id>.html', artwork_delete, name='artwork_delete'),
    path('collection/<int:id>', collection, name='artwork_collection'),
    re_path(
        r'^artist-autocomplete/$',
        ArtistAutocomplete.as_view(),
        name='artist-autocomplete',
    ),
    path('artist/<int:id>.html', artist_artworks, name='artist_artworks'),
]

# TODO: do not expose autocomplete publicly without permission check

#    path(r'^artist-autocomplete/', ArtistAutocomplete.as_view(),
    #    name='artist-autocomplete'
    #),