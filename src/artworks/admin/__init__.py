from mptt.admin import MPTTModelAdmin

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.widgets import get_select2_language
from django.db import models
from django.forms import Media, Textarea, TextInput
from django.urls import path
from django.utils.html import escape, format_html
from django.utils.translation import gettext_lazy as _

from ..models import Artwork, DiscriminatoryTerm, Keyword, Location, Material, Person
from .filters import (
    ArtistFilter,
    AuthorFilter,
    DiscriminatoryTermsFilter,
    GraphicDesignerFilter,
    PhotographerFilter,
)
from .forms import ArtworkAdminForm
from .utils import external_metadata_html
from .views import MultiArtworkCreationFormView


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
    search_fields = (
        'title',
        'title_english',
        'title_comment_de',
        'title_comment_en',
        'discriminatory_terms__term',
        'artists__name',
        'artists__synonyms',
        'photographers__name',
        'photographers__synonyms',
        'authors__name',
        'authors__synonyms',
        'graphic_designers__name',
        'graphic_designers__synonyms',
        'date',
        'material__name',
        'material__name_en',
        'material_description_de',
        'material_description_en',
        'dimensions_display',
        'keywords__name',
        'keywords__name_en',
        'place_of_production__name',
        'place_of_production__name_en',
        'place_of_production__synonyms',
        'location__name',
        'location__name_en',
        'location__synonyms',
        'comments_de',
        'comments_en',
        'credits',
        'credits_link',
        'link',
    )
    fields = (
        'published',
        'checked',
        'thumbnail_image',
        'image_original',
        'title',
        'title_english',
        'title_comment_de',
        'title_comment_en',
        'discriminatory_terms',
        'artists',
        'photographers',
        'authors',
        'graphic_designers',
        'date',
        'date_year_from',
        'date_year_to',
        'material',
        'material_description_de',
        'material_description_en',
        'width',
        'height',
        'depth',
        'dimensions_display',
        'keywords',
        'place_of_production',
        'location',
        'comments_de',
        'comments_en',
        'credits',
        'credits_link',
        'link',
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
        PhotographerFilter,
        AuthorFilter,
        GraphicDesignerFilter,
        DiscriminatoryTermsFilter,
        'published',
        'checked',
        'date_created',
        'date_changed',
    )
    change_list_template = 'admin/artworks/change_list.html'

    def get_urls(self):
        return [
            path(
                'multi-artwork-creation/',
                self.admin_site.admin_view(MultiArtworkCreationFormView.as_view()),
                name='multi-artwork-creation',
            ),
            *super().get_urls(),
        ]

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
                'admin/js/artwork_form.js',
            ),
            css={
                'screen': (
                    f'admin/css/vendor/select2/select2{extra}.css',
                    'admin/css/autocomplete.css',
                    'admin/css/artwork_form.css',
                ),
            },
        )

    @admin.display(description=_('Artists'))
    def get_artists(self, obj):
        return format_html('<br>'.join([escape(a.name) for a in obj.artists.all()]))

    def thumbnail_image(self, obj):
        if obj.image_fullsize:
            return format_html(
                '<img src="{url}" />'.format(
                    url=obj.image_fullsize.thumbnail['180x180'],
                ),
            )
        else:
            return format_html('none')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    exclude = ('external_metadata',)
    readonly_fields = (
        'synonyms_old',
        'date_created',
        'date_changed',
        'external_metadata_json',
    )
    list_display = ('name', 'gnd_id', 'gnd_overwrite', 'date_created', 'date_changed')
    ordering = ('-date_created',)
    search_fields = (
        'name',
        'synonyms',
        'gnd_id',
    )
    list_filter = ('date_created', 'date_changed')

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(Keyword)
class KeywordAdmin(MPTTModelAdmin):
    exclude = ('external_metadata',)
    readonly_fields = ('external_metadata_json',)
    list_display = ('name', 'getty_id', 'getty_overwrite')
    search_fields = (
        'name',
        'name_en',
        'getty_id',
    )

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(Location)
class LocationAdmin(MPTTModelAdmin):
    exclude = ('external_metadata',)
    readonly_fields = ('synonyms_old', 'external_metadata_json')
    autocomplete_fields = ('parent',)
    list_display = ('name', 'gnd_id', 'gnd_overwrite')
    search_fields = (
        ['gnd_id']
        + ['parent__' * i + 'name' for i in range(settings.LOCATION_SEARCH_LEVELS)]
        + ['parent__' * i + 'name_en' for i in range(settings.LOCATION_SEARCH_LEVELS)]
        + ['parent__' * i + 'synonyms' for i in range(settings.LOCATION_SEARCH_LEVELS)]
    )

    @admin.display
    def external_metadata_json(self, obj):
        return external_metadata_html(obj.external_metadata)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en')
    search_fields = ('name', 'name_en')


@admin.register(DiscriminatoryTerm)
class DiscriminatoryTermAdmin(admin.ModelAdmin):
    list_display = ('term',)
    search_fields = ('term',)
