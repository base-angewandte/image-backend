from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Repair image_original path for all artworks'

    def handle(self, *args, **options):
        for artwork in Artwork.objects.all():
            artwork.update_image_original_path()

        self.stdout.write(self.style.SUCCESS('DONE'))
