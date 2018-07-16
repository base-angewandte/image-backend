from django.urls import path
from artworks.views import *

urlpatterns = [
    path('', index, name='artworks_list'),
    path('<int:id>.json', details, name='artwork_details'),
    path('<int:id>_overlay.html', artwork_overlay_only, name='artwork_overlay_only'),
    path('<int:id>.html', artwork, name='artwork'),    
    path('artwork_new.html', artwork_new, name='artwork_new'),
    path('edit/<int:id>.html', artwork_edit, name='artwork_edit'),
    path('delete/<int:id>.html', artwork_delete, name='artwork_delete'),
    path('collection/<int:id>', collection, name='artwork_collection')
]
