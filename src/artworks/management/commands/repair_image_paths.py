from rich.progress import track

from django.conf import settings
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Repair image_original path for all artworks'

    def handle(self, *args, **options):
        for artwork in track(
            Artwork.objects.iterator(),
            description='Repairing paths...',
            complete_style=settings.PROGRESS_STYLES['complete'],
            total=Artwork.objects.count(),
        ):
            if artwork.image_original:
                artwork.update_image_original_path()
            else:
                self.stdout.write(
                    self.style.WARNING(f'Artwork {artwork.pk} has no image_original'),
                )

        self.stdout.write(self.style.SUCCESS('DONE'))
