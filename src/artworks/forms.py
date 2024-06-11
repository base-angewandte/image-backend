import re
from datetime import datetime

import requests
from dal import autocomplete

from django import forms
from django.conf import settings

# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from artworks.models import Album, Artist, Artwork, Keyword


class ArtworkForm(forms.ModelForm):
    image_original = forms.ImageField(
        label_suffix='', label='Upload', widget=forms.FileInput, required=False
    )
    image_original.widget.attrs.update({'class': 'imageselector'})

    class Meta:
        model = Artwork
        exclude = ['id', 'created_at', 'updated_at']
        widgets = {
            'artists': autocomplete.ModelSelect2Multiple(url='artist-autocomplete'),
            'keywords': autocomplete.ModelSelect2Multiple(url='keyword-autocomplete'),
            'title': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
            'title_english': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
        }
        # TODO: add and customize 'locationOfCreation': Select2Widget,

    def __init__(self, *args, **kwargs):
        # remove hard-coded help_text for ManyToManyFields that use a SelectMultiple widget
        # see 10 year old ticket: https://code.djangoproject.com/ticket/9321
        super().__init__(*args, **kwargs)
        self.fields['artists'].help_text = ''
        self.fields['keywords'].help_text = ''


class MPTTMultipleChoiceField(ModelMultipleChoiceField):
    # https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
    def label_from_instance(self, obj):
        level = getattr(
            obj, getattr(self.queryset.model._meta, 'level_attr', 'level'), 0
        )
        return '{} {}'.format('-' * level, force_str(obj))


class ArtistAdminForm(forms.ModelForm):
    def clean(self):
        if not self.data['name'] and not self.data['gnd_id']:
            raise forms.ValidationError(
                message=_('Either a name or a valid GND ID need to be set')
            )
        if self.data['gnd_id']:
            if not re.match(r'^[0-9]*(-?[0-9X])?$', self.data['gnd_id']):
                raise forms.ValidationError(message=_('Invalid GND ID format.'))

            cleaned_data = super().clean()
            gnd_id = self.data['gnd_id']
            try:
                response = requests.get(
                    settings.GND_BASE_URL + gnd_id,
                    timeout=settings.REQUESTS_TIMEOUT,
                )
            except requests.RequestException as e:
                raise forms.ValidationError(
                    _('Request error when retrieving GND data. Details: %(details)s'),
                    params={'details': f'{repr(e)}'},
                ) from e

            if response.status_code != 200:
                if response.status_code == 404:
                    raise forms.ValidationError(
                        _('No GND entry was found with ID %(id)s.'),
                        params={'id': gnd_id},
                    )
                raise forms.ValidationError(
                    _('HTTP error %(status)s when retrieving GND data: %(details)s'),
                    params={'status': response.status_code, 'details': response.text},
                )
            gnd_data = response.json()
            self.instance.external_metadata['gnd'] = {
                'date_requested': datetime.now().isoformat(),
                'response_data': gnd_data,
            }

            # TODO: discuss how exactly to handle name and synonym fields:
            #   based on which gnd data properties, in which formatting, how many synonyms
            #   and should we handle potential multiple names or dates?

            if 'preferredNameEntityForThePerson' in gnd_data:
                cleaned_data['name'] = (
                    gnd_data['preferredNameEntityForThePerson']['forename'][0]
                    + ' '
                    + gnd_data['preferredNameEntityForThePerson']['surname'][0]
                )
            elif 'preferredName' in gnd_data:
                cleaned_data['name'] = gnd_data['preferredName']

            if 'variantName' in gnd_data:
                cleaned_data['synonyms'] = ' | '.join(gnd_data['variantName'])[:255]

            if 'dateOfBirth' in gnd_data:
                cleaned_data['date_birth'] = gnd_data.get('dateOfBirth')[0]
            if 'dateOfDeath' in gnd_data:
                cleaned_data['date_death'] = gnd_data.get('dateOfDeath')[0]


class ArtworkAdminForm(forms.ModelForm):
    keywords = MPTTMultipleChoiceField(
        Keyword.objects.all(),
        widget=FilteredSelectMultiple(_('Keywords'), False),
        required=False,
    )

    artists = MPTTMultipleChoiceField(
        Artist.objects.all(),
        widget=FilteredSelectMultiple(_('Artists'), False),
        required=False,
    )

    class Meta:
        model = Artwork
        fields = '__all__'
        labels = {'Keywords': _('Keywords'), 'Artists': _('Artists')}


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        exclude = ['id', 'created_at', 'updated_at', 'user', 'artworks']


# Multi File Upload
# from https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/#uploading-multiple-files


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ImageFieldForm(forms.Form):
    image_field = MultipleImageField(label=_('Images'))
