from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from artworks.models import *
from artworks.forms import ArtworkForm, ArtworkAdminForm

# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
from django.contrib.admin.widgets import FilteredSelectMultiple
from .mptt_m2m_admin import MPTTMultipleChoiceField
from dal import autocomplete

class ArtworkAdmin(admin.ModelAdmin):
    form = ArtworkAdminForm
    readonly_fields = ('createdAt','updatedAt')

    """keywords = MPTTMultipleChoiceField(
        Keyword.objects.all(), 
        widget=FilteredSelectMultiple('Keywords', False),
        required=False
    )"""

    class Media:
        js = ['js/artwork_form.js']

admin.site.register(ArtworkCollection)
admin.site.register(Artist)
admin.site.register(Artwork, ArtworkAdmin)
admin.site.register(Keyword, MPTTModelAdmin) 

