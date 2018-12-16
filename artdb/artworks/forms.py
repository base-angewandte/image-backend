from django import forms
from django.contrib import admin
from django.forms import ModelMultipleChoiceField
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from dal import autocomplete
from artworks.models import Artwork, Keyword
# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
from django.contrib.admin.widgets import FilteredSelectMultiple

class ArtworkForm(forms.ModelForm):
    # TODO: localization
    # https://docs.djangoproject.com/en/2.0/topics/forms/modelforms/
  
    imageOriginal = forms.ImageField(label_suffix='', label='Upload', widget=forms.FileInput, required=False)
    imageOriginal.widget.attrs.update({'class': 'imageselector'})

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


class MPTTMultipleChoiceField(ModelMultipleChoiceField):
    # https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
    def label_from_instance(self, obj):
        level = getattr(obj, getattr(self.queryset.model._meta, 'level_attr', 'level'), 0)
        return u'%s %s' % ('-'*level, smart_text(obj))


class ArtworkAdminForm(forms.ModelForm):
    keywords = MPTTMultipleChoiceField(
        Keyword.objects.all(), 
        widget=FilteredSelectMultiple('Keywords', False),
        required=False
    )

    class Meta:
        model = Artwork
        fields = '__all__'

