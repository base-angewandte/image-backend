from mptt.admin import MPTTModelAdmin

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import get_select2_language
from django.db import models
from django.forms import Media, Textarea, TextInput
from django.utils.html import escape, format_html
from django.utils.translation import gettext_lazy as _

from ..models import Artwork, DiscriminatoryTerm, Keyword, Location, Person
from .filters import ArtistFilter
from .forms import ArtworkAdminForm
from .utils import external_metadata_html


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
        'discriminatory_terms',
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
    change_list_template = 'admin/artworks/change_list.html'

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        i18n_name = get_select2_language()
        i18n_file = (
            (f'admin/js/vendor/select2/i18n/{i18n_name}.js',) if i18n_name else ()
        )
        return Media(
            js=(
                f'admin/js/vendor/jquery/jquery{extra}.js',
                f'admin/js/vendor/select2/select2.full{extra}.js',
                *i18n_file,
                'admin/js/jquery.init.js',
                'js/artwork_form.js',
            ),
            css={
                'screen': (
                    f'admin/css/vendor/select2/select2{extra}.css',
                    'admin/css/autocomplete.css',
                ),
            },
        )

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


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
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
