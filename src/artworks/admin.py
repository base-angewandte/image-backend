import json

from admin_auto_filters.filters import AutocompleteFilter
from mptt.admin import MPTTModelAdmin

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import escape, format_html
from django.utils.translation import gettext_lazy as _

from .forms import ArtworkAdminForm
from .models import Artist, Artwork, DiscriminatoryTerm, Keyword, Location
from .views import ArtworkArtistAutocomplete


def external_metadata_html(external_metadata):
    value = json.dumps(external_metadata, indent=2, ensure_ascii=False)
    style = static('highlight/styles/intellij-light.min.css')
    js = static('highlight/highlight.min.js')

    return format_html(
        '<pre style="max-height:300px"><code class="language-json">{}</code></pre>'
        '<link rel="stylesheet" href="{}">'
        '<script src="{}"></script>'
        '<script>hljs.highlightAll();</script>',
        value,
        style,
        js,
    )


class ArtistFilter(AutocompleteFilter):
    title = _('Artist')
    field_name = 'artists'

    def get_autocomplete_url(self, request, model_admin):
        return reverse('admin:artwork-artist-autocomplete')


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
        'date_created',
        'date_changed',
    )
    change_list_template = 'admin/artwork/change_list.html'

    class Media:
        js = ['js/artwork_form.js']

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                'artwork-artist-autocomplete/',
                self.admin_site.admin_view(
                    ArtworkArtistAutocomplete.as_view(model_admin=self),
                ),
                name='artwork-artist-autocomplete',
            ),
            *urls,
        ]

    @admin.display(description=_('Artists'))
    def get_artists(self, obj):
        return format_html('<br>'.join([escape(a.name) for a in obj.artists.all()]))

    def thumbnail_image(self, obj):
        if obj.image_original:
            return format_html(
                '<img src="{url}" />'.format(
                    url=obj.image_original.thumbnail['180x180'],
                ),
            )
        else:
            return format_html('none')


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    exclude = ['external_metadata']
    readonly_fields = ('date_created', 'date_changed', 'external_metadata_json')
    list_display = ('name', 'gnd_id', 'gnd_overwrite', 'date_created', 'date_changed')
    ordering = ('-date_created',)
    search_fields = [
        'name',
    ]
    list_filter = ('date_created', 'date_changed')

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(Keyword)
class KeywordAdmin(MPTTModelAdmin):
    exclude = ['external_metadata']
    readonly_fields = ['external_metadata_json']
    list_display = ['name', 'getty_id', 'getty_overwrite']
    search_fields = ['name']

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(Location)
class LocationAdmin(MPTTModelAdmin):
    exclude = ['external_metadata']
    readonly_fields = ['external_metadata_json']
    list_display = ('name', 'gnd_id', 'gnd_overwrite')
    search_fields = [
        'parent__' * i + 'name' for i in range(settings.LOCATION_SEARCH_LEVELS)
    ]

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(DiscriminatoryTerm)
class DiscriminatoryTermAdmin(admin.ModelAdmin):
    list_display = ('term',)
    search_fields = ['term']
