from pathlib import Path

from PIL import Image, UnidentifiedImageError

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Check all Artwork image files and repair incorrect file extensions.'

    def handle(self, *args, **kwargs):
        image_not_found = []
        pil_verified_images = []
        pil_not_verified_images = []
        error_loading_images = []
        renamed_images = []

        # Loop through all Artwork objects
        for artwork in Artwork.objects.all():
            try:
                # Get the path to the image file
                image_path = Path(artwork.image_original.path)
                # Extract the file extension
                file_extension = image_path.suffix.lower()
            except (ObjectDoesNotExist, ValueError):
                image_not_found.append(artwork.id)
                continue
            try:
                with Image.open(image_path) as img:
                    img.verify()
                    pil_verified_images.append(image_path)
                    img_format = img.format
            except UnidentifiedImageError:
                pil_not_verified_images.append((artwork.id, image_path))
                continue
            except Exception:
                error_loading_images.append((artwork.id, image_path))
                continue

            if file_extension not in settings.PIL_VALID_EXTENSIONS[img_format]:
                new_image_path = image_path.with_suffix(
                    settings.PIL_VALID_EXTENSIONS[img_format][0],
                )
                image_path.rename(new_image_path)
                renamed_images.append((artwork.id, image_path, new_image_path))
                artwork.image_original.name = str(
                    new_image_path.relative_to(
                        Path(artwork.image_original.storage.location),
                    ),
                )
                artwork.save()

        if image_not_found:
            self.stdout.write(
                self.style.WARNING(
                    f'No image found for {len(image_not_found)} artworks:',
                ),
            )
            for artwork_id in image_not_found:
                self.stdout.write(f'Artwork ID {artwork_id}')

        if pil_not_verified_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Detected unverified image formats in {len(pil_not_verified_images)} cases:',
                ),
            )
            for artwork_id, path in pil_not_verified_images:
                self.stdout.write(f'Artwork {artwork_id}: {path}')

        if error_loading_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Detected unverified image errors in {len(error_loading_images)} cases:',
                ),
            )
            for artwork_id, path in error_loading_images:
                self.stdout.write(f'Artwork {artwork_id}: {path}')

        if renamed_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Renamed images with false endings in {len(renamed_images)} cases:',
                ),
            )
            for artwork_id, old_path, new_path in renamed_images:
                self.stdout.write(
                    f'Artwork {artwork_id}: renamed {old_path} to {new_path}',
                )
