from django import forms
from artworks.models import Artwork, Keyword
from dal import autocomplete

# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
from django.contrib.admin.widgets import FilteredSelectMultiple
from .mptt_m2m_admin import MPTTMultipleChoiceField

class ArtworkForm(forms.ModelForm):
    # TODO: localization
    # https://docs.djangoproject.com/en/2.0/topics/forms/modelforms/
  
    imageOriginal = forms.ImageField(label_suffix='', label='Upload', widget=forms.FileInput, required=False)
    imageOriginal.widget.attrs.update({'class': 'imageselector'})

    keywords = MPTTMultipleChoiceField(
        Keyword.objects.all(), 
        widget=FilteredSelectMultiple('Keywords', False),
        required=False
    )

    class Meta:
        model = Artwork
        exclude = ['id', 'createdAt', 'updatedAt']
        widgets = {
            'artists': autocomplete.ModelSelect2Multiple(url='artist-autocomplete'),
            'keywords': autocomplete.ModelSelect2Multiple(url='keyword-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        # remove hard-coded help_text for ManyToManyFields that use a SelectMultiple widget
        # see 10 year old ticket: https://code.djangoproject.com/ticket/9321
        super(ArtworkForm, self).__init__(*args, **kwargs)
        self.fields['artists'].help_text = ''
        self.fields['keywords'].help_text = ''
