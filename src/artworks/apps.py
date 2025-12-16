from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class ArtworksConfig(AppConfig):
    name = 'artworks'
    verbose_name = _('Image Content')

    def ready(self):
        # import signal handlers
        from . import signals

        post_migrate.connect(signals.post_migrate_signal, sender=self)
