from django import forms
from artworks.models import Artwork

class ArtworkForm(forms.ModelForm):
    # TODO: localization
    # https://docs.djangoproject.com/en/2.0/topics/forms/modelforms/
  
    original = forms.ImageField(label_suffix='', label='Upload', widget=forms.FileInput)
    original.widget.attrs.update({'class': 'imageselector'})

    class Meta:
        model = Artwork
        exclude = ['id','createdAt','updatedAt']
        # labels = {
           # "original": "Upload"
        # }
