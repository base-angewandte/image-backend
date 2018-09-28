from django import forms
from artworks.models import Artwork
from dal import autocomplete

class ArtworkForm(forms.ModelForm):
    # TODO: localization
    # https://docs.djangoproject.com/en/2.0/topics/forms/modelforms/
  
    imageOriginal = forms.ImageField(label_suffix='', label='Upload', widget=forms.FileInput, required=False)
    imageOriginal.widget.attrs.update({'class': 'imageselector'})

    class Meta:
        model = Artwork
        exclude = ['id', 'createdAt', 'updatedAt']
        widgets = {
            #'artists': autocomplete.ModelSelect2
            'artists': autocomplete.ModelSelect2Multiple
            (url='artist-autocomplete')
        }