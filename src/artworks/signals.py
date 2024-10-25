from pathlib import Path

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Artwork, convert_to_fullsize_image, get_path_to_original_file


@receiver(post_save, sender=Artwork)
def update_search_vector(sender, instance, created, *args, **kwargs):
    instance.update_search_vector()


@receiver(post_save, sender=Artwork)
def move_uploaded_image(sender, instance, created, **kwargs):
    """Move the uploaded image after an Artwork instance has been created."""
    if created:
        imagefile = instance.image_original
        old_name = imagefile.name
        relative_path = instance.image_original.storage.get_available_name(
            get_path_to_original_file(instance, old_name),
            max_length=sender._meta.get_field('image_original').max_length,
        )
        absolute_path = settings.MEDIA_ROOT_PATH / relative_path

        if not old_name:
            return

        if not absolute_path.exists():
            absolute_path.parent.mkdir(parents=True, exist_ok=True)

        # move the uploaded image
        Path(imagefile.path).rename(absolute_path)

        imagefile.name = relative_path
        instance.save()


@receiver(pre_save, sender=Artwork)
def update_fullsize_image(sender, instance, *args, **kwargs):
    """This signal is used to update an image_fullsize, in the case of a change
    in image_original."""
    if instance.pk:
        # I'm leaving this here as an alternative of checking if image_original was updated.
        # It could be done through the path or through the name.
        #     old_artwork = Artwork.objects.get(pk=instance.pk)
        #     if old_artwork.image_original.path != instance.image_original.path:
        #         convert_to_fullsize_image(instance, instance.image_original.path)
        old_instance = Artwork.objects.get(pk=instance.pk)
        if old_instance.image_original.name != instance.image_original.name:
            convert_to_fullsize_image(instance, instance.image_original.path)


@receiver(post_save, sender=Artwork)
def create_image_original(sender, instance, created, *args, **kwargs):
    """This signal is used to create an image_fullsize, when the image_original
    is created."""
    if created and instance.image_original:
        image_original_path = instance.image_original.path
        convert_to_fullsize_image(instance, image_original_path)
