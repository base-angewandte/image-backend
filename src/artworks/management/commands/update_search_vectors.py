from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Update search vector for all artworks'

    def handle(self, *args, **options):
        for artwork in Artwork.objects.all():
            artwork.update_search_vector()

        self.stdout.write(self.style.SUCCESS('DONE'))
