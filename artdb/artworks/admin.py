from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm, ArtworkAdminForm
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin


class ArtworkCollectionMembershipInline(OrderedTabularInline):
    model = ArtworkCollectionMembership
    autocomplete_fields = ['artwork']
    extra = 0
    fields = ('artwork', 'connected_with', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)


class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    list_display = ('title', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['title']
    fields = ('published', 'checked', 'thumbnail_image', 'image_original', 'title', 'title_english', 'artists', 'date', 'date_year_from', 'date_year_to', 'material', 'dimensions', 'credits', 'keywords', 'location_of_creation', 'location_current', 'created_at', 'updated_at',)
    readonly_fields = ('created_at','updated_at', 'thumbnail_image')

    class Media:
        js = ['js/artwork_form.js']

    def thumbnail_image(self, obj):
        if obj.image_original:
            return format_html('<img src="{url}" />'.format(url = obj.image_original.thumbnail['180x180']))
        else:
            return format_html('none')


class ArtworkCollectionAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    readonly_fields = ('created_at','updated_at')
    list_display = ('title', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['title']
    inlines = (ArtworkCollectionMembershipInline,)


class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at','updated_at')
    list_display = ('name', 'created_at', 'updated_at')
    ordering = ('-created_at',)
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
