from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm, ArtworkAdminForm


from django.contrib.admin.widgets import FilteredSelectMultiple
from dal import autocomplete

class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    readonly_fields = ('createdAt','updatedAt')

    class Media:
        js = ['js/artwork_form.js']

admin.site.register(ArtworkCollection)
admin.site.register(Artist)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, MPTTModelAdmin) 

