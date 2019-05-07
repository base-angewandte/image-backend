from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ArtworksConfig(AppConfig):
    name = 'artworks'
    verbose_name = _('Image Content')
