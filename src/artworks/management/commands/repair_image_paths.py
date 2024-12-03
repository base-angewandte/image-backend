from django.core.management.base import BaseCommand

from artworks.models import Artwork
from artworks.signals import update_image_original_path


class Command(BaseCommand):
    help = 'Repair image_original path for all artworks'

    def handle(self, *args, **options):
        for artwork in Artwork.objects.all():
            update_image_original_path(artwork)
            artwork.save(update_fields=['image_original'])

        self.stdout.write(self.style.SUCCESS('DONE'))
