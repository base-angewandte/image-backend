from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Artwork, convert_to_fullsize_image


@receiver(post_save, sender=Artwork)
def update_search_vector(sender, instance, created, *args, **kwargs):
    instance.update_search_vector()


@receiver(pre_save, sender=Artwork)
def update_fullsize_image(sender, instance, *args, **kwargs):
    if instance.pk:
        #     old_artwork = Artwork.objects.get(pk=instance.pk)
        #     if old_artwork.image_original.path != instance.image_original.path:
        #         convert_to_fullsize_image(instance, instance.image_original.path)
        old_instance = Artwork.objects.get(pk=instance.pk)
        if old_instance.image_original.name != instance.image_original.name:
            convert_to_fullsize_image(instance, instance.image_original.path)


@receiver(post_save, sender=Artwork)
def create_image_original(sender, instance, created, *args, **kwargs):
    if created and instance.image_original:
        image_original_path = instance.image_original.path
        convert_to_fullsize_image(instance, image_original_path)
