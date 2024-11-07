from pathlib import Path

from django.conf import settings
from django.db import connection, migrations

prefix_old = 'artworks/imageOriginal'
prefix_new = 'artworks/image_original'


def move_images(apps, schema_editor):
    from artworks.models import Artwork
    for artwork in Artwork.objects.all():
        image = artwork.image_original
        if image and Path(image.path).exists():
            image.delete_all_created_images()
            old = image.name
            if old.startswith(prefix_old):
                old_path = settings.MEDIA_ROOT_PATH / old
                new = f'{prefix_new}/{artwork.pk}/{old_path.name}'
                new_path = settings.MEDIA_ROOT_PATH / new
                new_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.rename(new_path)
                image.name = new
                artwork.save()


def move_images_reverse(apps, schema_editor):
    from artworks.models import Artwork
    for artwork in Artwork.objects.all():
        image = artwork.image_original
        if image and Path(image.path).exists():
            image.delete_all_created_images()
            new = image.name
            if new.startswith(prefix_new):
                new_path = settings.MEDIA_ROOT_PATH / new
                old = f'{prefix_old}/{artwork.pk}/{new_path.name}'
                old_path = settings.MEDIA_ROOT_PATH / old
                old_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.rename(old_path)
                image.name = old
                artwork.save()


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0093_alter_artwork_image_original_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=move_images, reverse_code=move_images_reverse
        ),
    ]
