from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm

class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkForm
    readonly_fields = ('createdAt','updatedAt')
    class Media:
        js = ['js/artwork_form.js']

admin.site.register(ArtworkCollection)
admin.site.register(Artist)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, MPTTModelAdmin) 