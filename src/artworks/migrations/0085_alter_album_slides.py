import shortuuid

from django.db import migrations


def add_slide_ids(apps, schema_editor):
    Album = apps.get_model('artworks', 'Album')
    for album in Album.objects.all():
        new_slides = []
        for slide in album.slides:
            new_slides.append({
                'id': shortuuid.uuid(),
                'items': slide,
            })
        album.slides = new_slides
        album.save()


def remove_slide_ids(apps, schema_editor):
    Album = apps.get_model('artworks', 'Album')
    for album in Album.objects.all():
        old_slides = []
        for slide in album.slides:
            old_slides.append(slide['items'])
        album.slides = old_slides
        album.save()


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0084_alter_artwork_material_old_alter_person_date_display'),
    ]

    operations = [
        migrations.RunPython(
            code=add_slide_ids, reverse_code=remove_slide_ids
        ),
    ]
