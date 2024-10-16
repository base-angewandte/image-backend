from pathlib import Path

from PIL import Image, UnidentifiedImageError

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Loops through all Artwork objects, extracts the paths of the images and changes them if necessary'

    def handle(self, *args, **kwargs):
        image_not_found = []
        pil_verified_images = []
        pil_not_verified_images = []
        error_loading_images = []
        renamed_images = []

        valid_extensions = {}
        for extension, img_format in Image.registered_extensions().items():
            if img_format not in valid_extensions:
                valid_extensions[img_format] = []
            valid_extensions[img_format].append(extension)

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
                pil_not_verified_images.append(image_path)
                continue
            except Exception:
                error_loading_images.append(image_path)
                continue

            if file_extension not in valid_extensions[img_format]:
                new_image_path = image_path.with_suffix(valid_extensions[img_format][0])
                image_path.rename(new_image_path)
                renamed_images.append(new_image_path)
                artwork.image_original.name = str(
                    new_image_path.relative_to(
                        Path(artwork.image_original.storage.location),
                    ),
                )
                artwork.save()

        if image_not_found:
            label = 'image'
            self.stdout.write(
                self.style.WARNING(
                    f'No {label} found for {len(image_not_found)} artworks:',
                ),
            )
            for artwork_id in image_not_found:
                self.stdout.write(f'Artwork ID {artwork_id}')

        if pil_not_verified_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Unverified image-formats were detected by PIL in {len(pil_not_verified_images)} cases:',
                ),
            )
            for entry in pil_not_verified_images:
                self.stdout.write(str(entry))

        if error_loading_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Unverified image-errors were detected in {len(error_loading_images)} cases:',
                ),
            )
            for entry in error_loading_images:
                self.stdout.write(str(entry))

        if renamed_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Images with false endings found in {len(renamed_images)} cases:',
                ),
            )
            for entry in renamed_images:
                self.stdout.write(str(entry))
