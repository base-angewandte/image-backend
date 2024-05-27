from dal_admin_filters import AutocompleteFilter
from mptt.admin import MPTTModelAdmin

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput
from django.utils.html import escape, format_html
from django.utils.translation import gettext_lazy as _

from .forms import ArtworkAdminForm
from .models import Album, Artist, Artwork, DiscriminatoryTerm, Keyword, Location


class ArtistFilter(AutocompleteFilter):
    title = _('Artist')
    field_name = 'artists'
    autocomplete_url = 'artwork-artist-autocomplete'


class CollectionListFilter(admin.SimpleListFilter):
    title = _('Folder')
    parameter_name = 'collection'

    def lookups(self, request, model_admin):
        users_collections = Album.objects.filter(user=request.user)
        return [(c.id, c.title) for c in users_collections]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(Album__id=self.value())
        else:
            return queryset


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    list_display = (
        'title',
        'get_artists',
        'checked',
        'published',
        'date_created',
        'date_changed',
    )
    ordering = ('-date_created',)
    search_fields = ['title']
    fields = (
        'published',
        'checked',
        'thumbnail_image',
        'image_original',
        'title',
        'title_english',
        'title_comment',
        'artists',
        'date',
        'date_year_from',
        'date_year_to',
        'material',
        'dimensions',
        'keywords',
        'place_of_production',
        'location',
        'comments',
        'credits',
        'date_created',
        'date_changed',
    )
    readonly_fields = ('date_created', 'date_changed', 'thumbnail_image')
    autocomplete_fields = ('place_of_production', 'location')
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }
    list_filter = (
        ArtistFilter,
        'published',
        'checked',
        CollectionListFilter,
        'date_created',
        'date_changed',
    )

    class Media:
        js = ['js/artwork_form.js']

    @admin.display(description=_('Artists'))
    def get_artists(self, obj):
        return format_html('<br>'.join([escape(a.name) for a in obj.artists.all()]))

    def thumbnail_image(self, obj):
        if obj.image_original:
            return format_html(
                '<img src="{url}" />'.format(
                    url=obj.image_original.thumbnail['180x180']
                )
            )
        else:
            return format_html('none')


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ('date_created', 'date_changed')
    list_display = ('name', 'date_created', 'date_changed')
    ordering = ('-date_created',)
    search_fields = [
        'name',
    ]
    list_filter = ('date_created', 'date_changed')


@admin.register(Keyword)
class KeywordAdmin(MPTTModelAdmin):
    search_fields = ['name']


@admin.register(Location)
class LocationAdmin(MPTTModelAdmin):
    search_fields = [
        'parent__' * i + 'name' for i in range(settings.LOCATION_SEARCH_LEVELS)
    ]


@admin.register(DiscriminatoryTerm)
class DiscriminatoryTermAdmin(admin.ModelAdmin):
    list_display = ('term',)
    search_fields = ['term']
