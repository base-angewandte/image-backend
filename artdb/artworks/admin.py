from django.contrib import admin
from artworks.models import *
from artworks.forms import ArtworkForm

class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkForm
    class Media:
        js = ['js/artwork_form.js']

admin.site.register(ArtworkCollection)
admin.site.register(Artist)
admin.site.register(Artwork, ArtworkAdmin)