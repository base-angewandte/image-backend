from pathlib import Path

from django.conf import settings
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Artwork, get_path_to_original_file


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
def update_images(sender, instance, *args, **kwargs):
    """Manage `image_fullsize` updates based on changes to `image_original`.

    - If `image_original` is deleted, delete `image_fullsize` to maintain consistency.
    - If `image_original` is changed, delete renditions for both `image_original` and `image_fullsize`,
     then generate a new `image_fullsize` based on the updated `image_original`.
    - For new `Artwork` instances with `image_original` present, create `image_fullsize`.
    """
    if instance.pk:
        old_instance = Artwork.objects.get(pk=instance.pk)
        # Check if image_original was deleted
        if not instance.image_original and old_instance.image_original:
            instance.image_fullsize.delete(save=False)
        # I'm leaving this here as an alternative of checking if image_original was updated.
        # It could be done through the path or through the name.
        #     old_artwork = Artwork.objects.get(pk=instance.pk)
        #     if old_artwork.image_original.path != instance.image_original.path:
        #         convert_to_fullsize_image(instance, instance.image_original.path)
        # Check if image_original was changed and delete both old images and generate image_fullsize
        elif old_instance.image_original.name != instance.image_original.name:
            old_instance.image_original.delete_all_created_images()
            old_instance.image_fullsize.delete_all_created_images()
            instance.create_image_fullsize(save=False)
    else:
        # For new instances:
        if instance.image_original:
            instance.create_image_fullsize(save=False)


@receiver(post_delete, sender=Artwork)
def delete_artwork_images(sender, instance, **kwargs):
    """Delete Artwork's originalImage and all renditions on post_delete."""
    instance.image_original.delete_all_created_images()
    instance.image_original.delete(save=False)
    if instance.image_fullsize:
        instance.image_fullsize.delete_all_created_images()
        instance.image_fullsize.delete(save=False)
