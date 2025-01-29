import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Delete all empty media folders'

    def handle(self, *args, **options):
        # code from https://stackoverflow.com/a/65624165 and slightly adapted
        deleted = set()

        for current_dir, subdirs, files in os.walk(
            settings.MEDIA_ROOT_PATH,
            topdown=False,
        ):
            current_dir_path = Path(current_dir)
            still_has_subdirs = False
            for subdir in subdirs:
                if current_dir_path / subdir not in deleted:
                    still_has_subdirs = True
                    break

            if not any(files) and not still_has_subdirs:
                current_dir_path.rmdir()
                deleted.add(current_dir_path)

        self.stdout.write(self.style.SUCCESS('DONE'))
