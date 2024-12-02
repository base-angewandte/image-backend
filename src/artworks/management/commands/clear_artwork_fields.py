from django.core.management.base import BaseCommand

from artworks.models import Artwork
from artworks.utils import remove_non_printable_characters


class Command(BaseCommand):
    help = 'Clean Artwork fields by removing non-printable characters and replacing line breaks with spaces.'

    def handle(self, *args, **options):
        fields = ('title', 'title_english')

        cleaned = {f: [] for f in fields}

        for artwork in Artwork.objects.all():
            changed = False
            for f in fields:
                value = getattr(artwork, f)
                if value:
                    cleaned_value = remove_non_printable_characters(
                        value.replace('\r\n', ' ')
                        .replace('\n', ' ')
                        .replace('\r', ' '),
                    )

                    if cleaned_value != getattr(artwork, f):
                        setattr(artwork, f, cleaned_value)
                        changed = True
                        cleaned[f].append(artwork.id)
            if changed:
                artwork.save(update_fields=fields)

        for f in fields:
            if cleaned[f]:
                self.stdout.write(
                    self.style.WARNING(
                        f'The {f} attribute of {len(cleaned[f])} Artworks has been cleaned:',
                    ),
                )
                for artwork_id in cleaned[f]:
                    self.stdout.write(artwork_id)
