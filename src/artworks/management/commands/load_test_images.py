from random import choice
from shutil import copy

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from artworks.models import Artwork, get_path_to_original_file


class Command(BaseCommand):
    help = 'Use test images for artworks without images, based on image-placeholder-*.png in the MEDIA_ROOT_PATH.'

    def handle(self, *args, **options):
        test_images = [
            p
            for p in settings.MEDIA_ROOT_PATH.iterdir()
            if p.name.startswith('image-placeholder-') and p.name.endswith('.png')
        ]

        if not test_images:
            raise CommandError(
                f'No image-placeholder-*.png files found in {settings.MEDIA_ROOT_PATH}',
            )

        for artwork in Artwork.objects.filter(image_original=''):
            image = choice(test_images)  # noqa: S311 - we don't use this for cryptographic purposes
            dest = settings.MEDIA_ROOT_PATH / get_path_to_original_file(
                artwork,
                image.name,
            )
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy(image, dest)
            artwork.image_original.name = get_path_to_original_file(artwork, image.name)
            artwork.save()
