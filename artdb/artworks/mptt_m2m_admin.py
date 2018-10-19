from django.forms import ModelMultipleChoiceField
from django.utils.encoding import smart_text

# https://gist.github.com/tdsymonds/abdcb395f172a016ed785f59043749e3

class MPTTMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        level = getattr(obj, getattr(self.queryset.model._meta, 'level_attr', 'level'), 0)
        return u'%s %s' % ('-'*level, smart_text(obj))
