from base_common.models import AbstractBaseModel
from tinymce.models import HTMLField

from django.db import models


class Text(AbstractBaseModel):
    title = models.CharField(max_length=255, editable=False)
    de = HTMLField()
    en = HTMLField()

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title
