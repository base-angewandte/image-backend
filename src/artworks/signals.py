from pathlib import Path

from django.conf import settings
from django.db import connections
from django.db.migrations.loader import MigrationLoader
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
    """Creates, updates or deletes images of an Artwork if necessary.

    - Creates and updates `image_fullsize` if necessary.
    - Deletes `images_fullsize` if `image_original` has been deleted.
    - Deletes images created with VersatileImageField, if the image changes.
    """
    if instance._state.adding:
        # artwork has not been created yet

        if instance.image_original:
            instance.create_image_fullsize(save=False)
    else:
        old_instance = Artwork.objects.get(pk=instance.pk)

        image_original_created = (
            instance.image_original and not old_instance.image_original
        )
        image_original_changed = (
            instance.image_original
            and old_instance.image_original
            and old_instance.image_original.name != instance.image_original.name
        )
        image_original_deleted = (
            not instance.image_original and old_instance.image_original
        )

        # cleanup
        if image_original_deleted or image_original_changed:
            old_instance.image_original.delete_all_created_images()
            if old_instance.image_fullsize:
                old_instance.image_fullsize.delete_all_created_images()
                instance.image_fullsize.delete(save=False)

        # create or update image_fullsize
        if image_original_created or image_original_changed:
            instance.create_image_fullsize(save=False)


@receiver(post_delete, sender=Artwork)
def delete_artwork_images(sender, instance, **kwargs):
    """Delete Artwork's originalImage and all renditions on post_delete."""
    instance.image_original.delete_all_created_images()
    instance.image_original.delete(save=False)
    if instance.image_fullsize:
        instance.image_fullsize.delete_all_created_images()
        instance.image_fullsize.delete(save=False)


def post_migrate_updates(sender, **kwargs):
    plan = kwargs.get('plan')

    # check if a migration has been run and if it was forward
    if plan and not plan[0][1]:
        # get last migration
        last_migration = 0
        loader = MigrationLoader(connections['default'])

        for migration_app_label, migration_name in loader.disk_migrations:
            if migration_app_label == sender.name:
                migration_int = int(migration_name[:4])
                if migration_int > last_migration:
                    last_migration = migration_int

        for migration, _reverse in plan:
            if int(migration.name[:4]) == last_migration:
                for artwork in Artwork.objects.all():
                    # update search vector if there have been changes to the model
                    artwork.update_search_vector()
