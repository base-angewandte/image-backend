from dal import autocomplete

from django import forms

# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from artworks.models import Album, Artist, Artwork, DiscriminatoryTerm, Keyword


class ArtworkForm(forms.ModelForm):
    image_original = forms.ImageField(
        label_suffix='',
        label='Upload',
        widget=forms.FileInput,
        required=False,
    )
    image_original.widget.attrs.update({'class': 'imageselector'})

    class Meta:
        model = Artwork
        exclude = ['id', 'created_at', 'updated_at']  # noqa: DJ006
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
            obj,
            getattr(self.queryset.model._meta, 'level_attr', 'level'),
            0,
        )
        return '{} {}'.format('-' * level, force_str(obj))


class ArtworkAdminForm(forms.ModelForm):
    keywords = MPTTMultipleChoiceField(
        Keyword.objects.all(),
        widget=FilteredSelectMultiple(_('Keywords'), False),
        required=False,
    )

    artists = ModelMultipleChoiceField(
        Artist.objects.all(),
        widget=FilteredSelectMultiple(_('Artists'), False),
        required=False,
    )

    discriminatory_terms = ModelMultipleChoiceField(
        DiscriminatoryTerm.objects.all(),
        widget=FilteredSelectMultiple(_('Discriminatory terms'), False),
        required=False,
    )

    class Meta:
        model = Artwork
        fields = '__all__'  # noqa: DJ007
        labels = {'Keywords': _('Keywords'), 'Artists': _('Artists')}


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        exclude = ['id', 'created_at', 'updated_at', 'user', 'artworks']  # noqa: DJ006


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
        if isinstance(data, list | tuple):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ImageFieldForm(forms.Form):
    image_field = MultipleImageField(label=_('Images'))
