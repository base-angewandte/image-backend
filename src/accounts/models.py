from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    DISPLAY_IMAGES_MODES = ('crop', 'resize')
    DISPLAY_FOLDERS_MODES = ('list', 'grid')

    DISPLAY_IMAGES_CHOICES = [(m, m) for m in DISPLAY_IMAGES_MODES]
    DISPLAY_FOLDERS_CHOICES = [(m, m) for m in DISPLAY_FOLDERS_MODES]

    tos_accepted = models.BooleanField(default=False)
    display_images = models.CharField(
        choices=DISPLAY_IMAGES_CHOICES,
        default=DISPLAY_IMAGES_CHOICES[0][0],
    )
    display_folders = models.CharField(
        choices=DISPLAY_FOLDERS_CHOICES,
        default=DISPLAY_FOLDERS_CHOICES[0][0],
    )

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def preferences(self):
        return {
            'display_images': self.display_images,
            'display_folders': self.display_folders,
        }

    @property
    def is_editor(self):
        return self.groups.filter(name=settings.EDITOR_GROUP).exists()

    def __str__(self):
        return self.get_full_name() or self.username
