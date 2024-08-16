from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from ..models import Person


class ArtistFilter(SimpleListFilter):
    title = _('Artist')
    parameter_name = 'artist'
    query_filter = 'artists__id'
    template = 'admin/filters/filter-autocomplete.html'

    def lookups(self, request, model_admin):
        persons = [(str(person.id), person.name) for person in Person.objects.all()]
        return persons

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(**{self.query_filter: val})
