from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from ..models import DiscriminatoryTerm, Person


class PersonFilter(SimpleListFilter):
    title = _('Person')
    parameter_name = 'person'
    query_filter = 'person__id'
    template = 'admin/filters/filter-autocomplete.html'

    def lookups(self, request, model_admin):
        persons = [(str(person.id), person.name) for person in Person.objects.all()]
        return persons

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(**{self.query_filter: val})


class ArtistFilter(PersonFilter):
    title = _('Artist')
    parameter_name = 'artist'
    query_filter = 'artists__id'


class PhotographerFilter(PersonFilter):
    title = _('Photographer')
    parameter_name = 'photographers'
    query_filter = 'photographers__id'


class AuthorFilter(PersonFilter):
    title = _('Author')
    parameter_name = 'authors'
    query_filter = 'authors__id'


class GraphicDesignerFilter(PersonFilter):
    title = _('Graphic Designer')
    parameter_name = 'graphic_designers'
    query_filter = 'graphic_designers__id'


class DiscriminatoryTermsFilter(SimpleListFilter):
    title = _('Discriminatory Term')
    parameter_name = 'discriminatory_terms'
    query_filter = 'discriminatory_terms__id'
    template = 'admin/filters/filter-autocomplete.html'

    def lookups(self, request, model_admin):
        discriminatory_terms = [
            (str(dt.id), dt.term) for dt in DiscriminatoryTerm.objects.all()
        ]
        return discriminatory_terms

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(**{self.query_filter: val})
