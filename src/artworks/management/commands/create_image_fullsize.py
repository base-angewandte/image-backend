from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Populate image_fullsize for all artworks by converting from image_original'

    def handle(self, *args, **options):
        for artwork in Artwork.objects.all():
            if artwork.image_original:
                artwork.create_image_fullsize()
