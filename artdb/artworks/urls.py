from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog
from artworks.views import *

urlpatterns = [
    path('', artworks_list, name='artworks_list'),
    path('artwork/<int:id>.json', details, name='artwork_details'),
    path('artwork/<int:id>/detail_overlay.html', artwork_detail_overlay, name='artwork_detail_overlay'), 
    path('artwork/<int:id>/edit_overlay.html', artwork_edit, name='artwork_edit'),
    path('artwork/<int:id>/collect_overlay.html', artwork_collect, name='artwork_collect'),
    path('collection/<int:id>.html', collection, name='collection'),
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
        re_path(
        r'^keyword-autocomplete/$',
        KeywordAutocomplete.as_view(),
        name='keyword-autocomplete',
    ),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]