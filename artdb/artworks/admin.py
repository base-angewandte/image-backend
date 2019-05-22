from dal_admin_filters import AutocompleteFilter
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.utils.html import format_html, escape
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin

from .forms import ArtworkAdminForm
from .models import ArtworkCollectionMembership, ArtworkCollection, Artist, Artwork, Keyword, Location


class ArtworkCollectionMembershipInline(OrderedTabularInline):
    model = ArtworkCollectionMembership
    autocomplete_fields = ['artwork']
    extra = 0
    fields = ('artwork', )
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)


class ArtistFilter(AutocompleteFilter):
    title = _('Artist')
    field_name = 'artists'
    autocomplete_url = 'artwork-artist-autocomplete'


class CollectionListFilter(admin.SimpleListFilter):
    title = _('Folder')
    parameter_name = 'collection'

    def lookups(self, request, model_admin):
        users_collections = ArtworkCollection.objects.filter(user=request.user)
        return [(c.id, c.title) for c in users_collections]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(artworkcollection__id=self.value())
        else:
            return queryset


class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    list_display = ('title', 'get_artists', 'checked', 'published', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['title']
    fields = (
        'published',
        'checked',
        'thumbnail_image',
        'image_original',
        'title',
        'title_english',
        'artists',
        'date',
        'date_year_from',
        'date_year_to',
        'material',
        'dimensions',
        'keywords',
        'location_of_creation',
        'location_current',
        'description',
        'credits',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_image')
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 80})},
    }
    list_filter = (ArtistFilter, 'published', 'checked', CollectionListFilter, 'created_at', 'updated_at')

    class Media:
        js = ['js/artwork_form.js']

    def get_artists(self, obj):
        return format_html('<br>'.join([escape(a.name) for a in obj.artists.all()]))

    get_artists.short_description = _('Artists')

    def thumbnail_image(self, obj):
        if obj.image_original:
            return format_html('<img src="{url}" />'.format(url=obj.image_original.thumbnail['180x180']))
        else:
            return format_html('none')


class ArtworkCollectionAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('title', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['title']
    inlines = (ArtworkCollectionMembershipInline,)


class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_display = ('name', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ['name', ]
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
