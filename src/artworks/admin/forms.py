from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ModelMultipleChoiceField
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from ..models import Artwork, DiscriminatoryTerm, Keyword, Location, Material, Person


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
        Person.objects.all(),
        widget=FilteredSelectMultiple(_('Artists'), False),
        required=False,
    )

    photographers = ModelMultipleChoiceField(
        Person.objects.all(),
        widget=FilteredSelectMultiple(_('Photographers'), False),
        required=False,
    )

    authors = ModelMultipleChoiceField(
        Person.objects.all(),
        widget=FilteredSelectMultiple(_('Authors'), False),
        required=False,
    )

    graphic_designers = ModelMultipleChoiceField(
        Person.objects.all(),
        widget=FilteredSelectMultiple(_('Graphic designers'), False),
        required=False,
    )

    discriminatory_terms = ModelMultipleChoiceField(
        DiscriminatoryTerm.objects.all(),
        widget=FilteredSelectMultiple(_('Discriminatory terms'), False),
        required=False,
    )

    material = ModelMultipleChoiceField(
        Material.objects.all(),
        widget=FilteredSelectMultiple(_('Material/Technique'), False),
        required=False,
    )

    place_of_production = ModelMultipleChoiceField(
        Location.objects.all(),
        widget=FilteredSelectMultiple(_('Place of production'), False),
        required=False,
    )

    class Meta:
        model = Artwork
        fields = '__all__'  # noqa: DJ007
        labels = {'Keywords': _('Keywords'), 'Artists': _('Artists')}


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
