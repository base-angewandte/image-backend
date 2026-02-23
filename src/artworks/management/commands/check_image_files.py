import mimetypes
from pathlib import Path

import magic
from sorl.thumbnail import default

from django.conf import settings
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Check all Artwork image files and repair incorrect file extensions.'

    def handle(self, *args, **kwargs):
        image_not_found = []
        wand_verified_images = []
        wand_not_verified_images = []
        error_loading_images = []
        renamed_images = []
        not_allowed_mime_types = []

        # Loop through all Artwork objects
        for artwork in Artwork.objects.all():
            try:
                # Get the path to the image file
                image_path = Path(artwork.image_original.path)
                # Extract the file extension
            except ValueError:
                image_not_found.append(artwork.id)
                continue
            try:
                # checks based on file data
                with image_path.open('rb') as f:
                    # Detect MIME using python-magic
                    mime_type = magic.from_buffer(f.read(2048), mime=True)
                    # even though we don't need f here and this wouldn't need to be in
                    # the context block, perform this check before validating the file,
                    # as the latter is way more expensive
                    if mime_type not in settings.IM_ALLOWED_MIME_TYPES:
                        not_allowed_mime_types.append((artwork.id, image_path))
                        continue
                    # reset FP, as we just read from the file for magical reasons
                    f.seek(0)
                    ivi = default.engine.is_valid_image(f.read())
            except Exception as e:
                error_loading_images.append(
                    (artwork.id, image_path, type(e).__name__, str(e)),
                )
                continue
            if ivi:
                wand_verified_images.append(image_path)
            else:
                wand_not_verified_images.append((artwork.id, image_path))
                continue

            valid_extensions = mimetypes.guess_all_extensions(mime_type, strict=True)

            file_extension = image_path.suffix.lower()
            if valid_extensions and file_extension not in valid_extensions:
                new_image_path = image_path.with_suffix(
                    valid_extensions[0],
                )
                image_path.rename(new_image_path)
                renamed_images.append((artwork.id, image_path, new_image_path))
                artwork.image_original.name = str(
                    new_image_path.relative_to(
                        Path(artwork.image_original.storage.location),
                    ),
                )
                artwork.save(update_fields=['image_original'])

        if image_not_found:
            self.stdout.write(
                self.style.WARNING(
                    f'No image found for {len(image_not_found)} artworks:',
                ),
            )
            for artwork_id in image_not_found:
                self.stdout.write(f'Artwork ID {artwork_id}')

        if wand_not_verified_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Detected unverified image formats in {len(wand_not_verified_images)} cases:',
                ),
            )
            for artwork_id, path in wand_not_verified_images:
                self.stdout.write(f'Artwork {artwork_id}: {path}')

        if not_allowed_mime_types:
            self.stdout.write(
                self.style.WARNING(
                    f'Detected unverified mime types in {len(wand_not_verified_images)} cases:',
                ),
            )
            for artwork_id, path in wand_not_verified_images:
                self.stdout.write(f'Artwork {artwork_id}: {path}')

        if error_loading_images:
            self.stdout.write(
                self.style.WARNING(
                    f'Detected unverified image errors in {len(error_loading_images)} cases:',
                ),
            )
            for artwork_id, path, exc_type, exc_msg in error_loading_images:
                self.stdout.write(
                    f'Artwork {artwork_id}: {path} -> {exc_type}: {exc_msg}',
                )

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
