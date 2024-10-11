from pathlib import Path

from PIL import Image, UnidentifiedImageError

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Loops through all Artwork objects, extracts the paths of the images and changes them if necessary'

    def handle(self, *args, **kwargs):
        pil_verified_images = []
        pil_not_verified_images = []
        renamed_images = []
        # Loop through all Artwork objects
        for artwork in Artwork.objects.all():
            try:
                # Get the path to the image file
                image_path = Path(artwork.image_original.path)
                # Extract the file extension
                file_extension = image_path.suffix.lower()
            except (ObjectDoesNotExist, ValueError):
                self.stdout.write(
                    f'For Artwork ID {artwork.id}: No image was found or path is unavailable.',
                )
                continue
            try:
                with Image.open(image_path) as img:
                    img.verify()
                    pil_verified_images.append(image_path)
                    pil_extracted_extension = f'.{img.format.lower()}'
            except UnidentifiedImageError:
                self.stdout.write(
                    f'{image_path}: PIL cannot identify or load the image.',
                )
                pil_not_verified_images.append(image_path)
                continue
            except Exception as e:
                self.stdout.write(f'{image_path}: Error loading image with PIL: {e}')
                continue

            if pil_extracted_extension != file_extension:
                new_image_path = image_path.with_suffix(pil_extracted_extension)
                image_path.rename(new_image_path)
                renamed_images.append(new_image_path)

        if pil_not_verified_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Unverified image-formats were detected by PIL in {len(pil_not_verified_images)} cases:',
                ),
            )
            for entry in pil_not_verified_images:
                self.stdout.write(str(entry))

        if renamed_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Images with false endings found in {len(renamed_images)} cases:',
                ),
            )
            for entry in renamed_images:
                self.stdout.write(str(entry))
