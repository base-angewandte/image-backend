from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm, ArtworkAdminForm
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin


class ArtworkCollectionMembershipInline(OrderedTabularInline):
    model = ArtworkCollectionMembership
    autocomplete_fields = ['artwork']
    extra = 0
    fields = ('artwork', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)


class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('title', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    search_fields = ['title']
    # inlines = (ArtworkCollectionMembershipInline,)

    class Media:
        js = ['js/artwork_form.js']


class ArtworkCollectionAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('title', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    search_fields = ['title']
    inlines = (ArtworkCollectionMembershipInline,)


class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('createdAt','updatedAt')
    list_display = ('name', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    search_fields = ['name',]


class KeywordAdmin(MPTTModelAdmin):
    search_fields = ['name']


class LocationAdmin(MPTTModelAdmin):
    search_fields = ['name']


admin.site.register(ArtworkCollection, ArtworkCollectionAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Location, LocationAdmin)


