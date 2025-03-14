from versatileimagefield.datastructures import sizedimage

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def monkeypatch_versatile_image_field():
    """
    To bypass
    https://github.com/respondcreate/django-versatileimagefield/issues/59
    we monkey patch versatile image field to silent error when
    a specific setting is toggled
    """

    def dec(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except FileNotFoundError:
                if settings.DEBUG:
                    return
                raise

        return wrapper

    kls = sizedimage.SizedImage
    kls.create_resized_image = dec(kls.create_resized_image)


class ArtworksConfig(AppConfig):
    name = 'artworks'
    verbose_name = _('Image Content')

    def ready(self):
        # import signal handlers
        from . import signals

        post_migrate.connect(signals.post_migrate_signal, sender=self)

        if settings.DEBUG:
            monkeypatch_versatile_image_field()
