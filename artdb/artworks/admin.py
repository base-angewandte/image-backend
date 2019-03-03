from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.forms import TextInput, Textarea
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
    list_display = ('title', 'checked', 'published', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['title']
    fields = ('published', 'checked', 'thumbnail_image', 'image_original', 'title', 'title_english', 'artists', 'date', 'date_year_from', 'date_year_to', 'material', 'dimensions', 'keywords', 'location_of_creation', 'location_current', 'description', 'credits', 'created_at', 'updated_at')
    readonly_fields = ('created_at','updated_at', 'thumbnail_image')
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'80'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':80})},
    }
    list_filter = ('published', 'checked', 'created_at', 'updated_at')

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

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(ArtworkCollectionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.related_model == User:
            field.label_from_instance = self.get_user_label
        return field

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        field = super(ArtworkCollectionAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.related_model == User:
            field.label_from_instance = self.get_user_label
        return field

    def get_user_label(self, user):
        name = user.get_full_name()
        username = user.username

        return '{} ({})'.format(username, name) if name and name != username else username


class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at','updated_at')
    list_display = ('name', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['name',]
    list_filter = ('created_at', 'updated_at')


class KeywordAdmin(MPTTModelAdmin):
    search_fields = ['name']


class LocationAdmin(MPTTModelAdmin):
    search_fields = ['name']


admin.site.register(ArtworkCollection, ArtworkCollectionAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Location, LocationAdmin)
