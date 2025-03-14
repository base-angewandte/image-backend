from datetime import timedelta

import django_rq
from django_rq.queues import get_queue

from django.conf import settings
from django.db import connections
from django.db.migrations.loader import MigrationLoader
from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import (
    Artwork,
    Keyword,
    Location,
    Material,
    Person,
)
from .utils import remove_non_printable_characters


@receiver(pre_save, sender=Artwork)
def clean_artwork_titles(sender, instance, **kwargs):
    instance.title = remove_non_printable_characters(instance.title)
    instance.title_english = remove_non_printable_characters(instance.title_english)


@receiver(pre_save, sender=Artwork)
def update_images_pre_save(sender, instance, *args, **kwargs):
    """Creates, updates or deletes images of an Artwork if necessary.

    - Creates and updates `image_fullsize` if necessary.
    - Deletes `images_fullsize` if `image_original` has been deleted.
    - Deletes images created with VersatileImageField, if the image changes.
    """
    if not instance._state.adding:
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

        if image_original_deleted and old_instance.image_fullsize:
            old_instance.image_fullsize.delete_all_created_images()
            instance.image_fullsize.delete(save=False)

        # create or update image_fullsize
        if image_original_created or image_original_changed:
            instance.create_image_fullsize(save=False)


@receiver(post_save, sender=Artwork)
def update_images_post_save(sender, instance, created, **kwargs):
    """Change image_original path and create image_fullsize if necessary."""

    update_fields = []

    if instance.image_original:
        # update image original directory if it is not already correct
        if instance.pk not in instance.image_original.name:
            instance.update_image_original_path(save=False)
            update_fields.append('image_original')

        # create image fullsize if it doesn't exist yet
        if not instance.image_fullsize:
            instance.create_image_fullsize(save=False)
            update_fields.append('image_fullsize')

        if update_fields:
            instance.save(update_fields=update_fields)


@receiver(post_save, sender=Artwork)
def update_search_vector(sender, instance, created, *args, **kwargs):
    instance.update_search_vector()


@receiver(post_save, sender=Keyword)
def update_search_vector_keyword(sender, instance, created, *args, **kwargs):
    keyword_ids = (
        Keyword.objects.filter(pk=instance.pk)
        .get_ancestors(include_self=True)
        .values_list('pk', flat=True)
    )

    artwork_qs = Artwork.objects.filter(keywords__id__in=keyword_ids)

    for artwork in artwork_qs:
        django_rq.enqueue(
            artwork.update_search_vector,
            result_ttl=settings.RQ_RESULT_TTL,
        )


@receiver(post_save, sender=Material)
def update_search_vector_material(sender, instance, created, *args, **kwargs):
    artwork_ids = instance.artworks.values_list('pk', flat=True)

    for artwork in Artwork.objects.filter(id__in=artwork_ids):
        django_rq.enqueue(
            artwork.update_search_vector,
            result_ttl=settings.RQ_RESULT_TTL,
        )


@receiver(post_save, sender=Location)
def update_search_vector_location(sender, instance, created, *args, **kwargs):
    location_ids = (
        Location.objects.filter(pk=instance.pk)
        .get_ancestors(include_self=True)
        .values_list('pk', flat=True)
    )

    artwork_qs = Artwork.objects.filter(
        Q(place_of_production__id__in=location_ids) | Q(location__id__in=location_ids),
    )

    for artwork in artwork_qs:
        django_rq.enqueue(
            artwork.update_search_vector,
            result_ttl=settings.RQ_RESULT_TTL,
        )


@receiver(post_save, sender=Person)
def update_search_vector_person(sender, instance, created, *args, **kwargs):
    artwork_ids = []

    artwork_ids.extend(instance.artworks_artists.values_list('pk', flat=True))
    artwork_ids.extend(instance.artworks_photographers.values_list('pk', flat=True))
    artwork_ids.extend(instance.artworks_authors.values_list('pk', flat=True))
    artwork_ids.extend(instance.artworks_graphic_designers.values_list('pk', flat=True))

    for artwork in Artwork.objects.filter(id__in=artwork_ids):
        django_rq.enqueue(
            artwork.update_search_vector,
            result_ttl=settings.RQ_RESULT_TTL,
        )


@receiver(post_delete, sender=Artwork)
def delete_artwork_images(sender, instance, **kwargs):
    """Delete Artwork's originalImage and all renditions on post_delete."""
    instance.image_original.delete_all_created_images()
    instance.image_original.delete(save=False)
    if instance.image_fullsize:
        instance.image_fullsize.delete_all_created_images()
        instance.image_fullsize.delete(save=False)


def post_migrate_updates():
    for artwork in Artwork.objects.all():
        # update search vector if there have been changes to the model
        django_rq.enqueue(
            artwork.update_search_vector,
            result_ttl=settings.RQ_RESULT_TTL,
        )

        # create full size images, if they don't exist
        if artwork.image_original and not artwork.image_fullsize:
            django_rq.enqueue(
                artwork.create_image_fullsize,
                result_ttl=settings.RQ_RESULT_TTL,
            )


def post_migrate_signal(sender, **kwargs):
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
            # we only apply changes after the last migration has run to ensure that the
            # model is up to date
            if int(migration.name[:4]) == last_migration:
                if settings.RQ_ASYNC:
                    queue = get_queue('default')
                    queue.enqueue_in(
                        timedelta(seconds=5),
                        post_migrate_updates,
                        result_ttl=settings.RQ_RESULT_TTL,
                    )
                else:
                    django_rq.enqueue(
                        post_migrate_updates,
                        result_ttl=settings.RQ_RESULT_TTL,
                    )
