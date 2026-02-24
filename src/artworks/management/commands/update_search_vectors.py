from rich.progress import track

from django.conf import settings
from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Update search vector for all artworks'

    def handle(self, *args, **options):
        for artwork in track(
            Artwork.objects.iterator(),
            description='Updating search vectors...',
            complete_style=settings.PROGRESS_STYLES['complete'],
        ):
            artwork.update_search_vector()

        self.stdout.write(self.style.SUCCESS('DONE'))
