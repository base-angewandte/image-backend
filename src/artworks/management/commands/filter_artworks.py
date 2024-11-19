from django.core.management.base import BaseCommand

from artworks.models import Artwork, remove_non_printable_characters


class Command(BaseCommand):
    help = 'Clean Artwork titles by removing non-printable characters and replacing line breaks with spaces.'

    def handle(self, *args, **options):
        artworks = Artwork.objects.all()

        cleaned_titles = []
        cleaned_titles_english = []

        for artwork in artworks:
            # always check the titles of artworks, because they are a mandatory field
            original_title = artwork.title
            cleaned_title = artwork.title.replace('\n', ' ').replace('\r', ' ')
            cleaned_title = remove_non_printable_characters(cleaned_title)

            if artwork.title != original_title:
                artwork.title = cleaned_title
                cleaned_titles.append(artwork.title)

            # only apply filter to title_english, if it is available
            if artwork.title_english:
                original_title_english = artwork.title_english
                cleaned_title_english = artwork.title_english.replace(
                    '\n',
                    ' ',
                ).replace('\r', ' ')
                cleaned_title_english = remove_non_printable_characters(
                    cleaned_title_english,
                )

                if artwork.title_english != original_title_english:
                    artwork.title_english = cleaned_title_english
                    cleaned_titles_english.append(artwork.title_english)

            artwork.save()

        if cleaned_titles:
            self.stdout.write(
                self.style.WARNING(
                    f'The filter was applied to the following {len(cleaned_titles)} title:',
                ),
            )
            for entry in cleaned_titles:
                self.stdout.write(entry[0])

        if cleaned_titles_english:
            self.stdout.write(
                self.style.WARNING(
                    f'The filter was applied to the following {len(cleaned_titles_english)} title_english:',
                ),
            )
            for entry in cleaned_titles_english:
                self.stdout.write(entry[0])
