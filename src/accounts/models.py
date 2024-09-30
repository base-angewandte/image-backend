from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    DISPLAY_IMAGES_CHOICES = [('crop', 'crop'), ('resize', 'resize')]
    DISPLAY_FOLDERS_CHOICES = [('list', 'list'), ('grid', 'grid')]

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

    def __str__(self):
        return self.get_full_name() or self.username
