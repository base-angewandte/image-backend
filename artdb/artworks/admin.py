from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm, ArtworkAdminForm


class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('title', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)

    class Media:
        js = ['js/artwork_form.js']

class ArtworkCollectionAdmin(admin.ModelAdmin):
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('title', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    
class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('name', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)


admin.site.register(ArtworkCollection, ArtworkCollectionAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, MPTTModelAdmin)


