from django.core.management.base import BaseCommand

from artworks.models import Artwork


class Command(BaseCommand):
    help = 'Repair image_original path for all artworks'

    def handle(self, *args, **options):
        for artwork in Artwork.objects.all():
            if artwork.image_original:
                artwork.update_image_original_path()
            else:
                self.stdout.write(
                    self.style.WARNING(f'Artwork {artwork.pk} has no image_original'),
                )

        self.stdout.write(self.style.SUCCESS('DONE'))
