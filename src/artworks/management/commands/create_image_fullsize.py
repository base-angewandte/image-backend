from rich.progress import track

from django.conf import settings
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Populate image_fullsize for all artworks by converting from image_original'

    def handle(self, *args, **options):
        for artwork in track(
            Artwork.objects.iterator(),
            description='(Re)creating image_fullsize for all artworks...',
            complete_style=settings.PROGRESS_STYLES['complete'],
        ):
            if artwork.image_original:
                artwork.create_image_fullsize()
