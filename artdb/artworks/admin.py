from django.contrib import admin
from artworks.models import *

admin.site.register(Artwork)
admin.site.register(ArtworkCollection)
admin.site.register(ArtworkCollectionMembership)
admin.site.register(Artist)