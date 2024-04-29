from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Artwork


@receiver(post_save, sender=Artwork)
def update_search_vector(sender, instance, created, *args, **kwargs):
    instance.update_search_vector()
