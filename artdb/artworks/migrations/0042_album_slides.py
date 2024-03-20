# Generated by Django 2.2.1 on 2023-05-03 09:24

import django.contrib.postgres.fields.jsonb
from django.db import migrations


def create_slides_content(apps, schema_editor):
    """Generates slides content from the AlbumMembership relations"""
    Album = apps.get_model('artworks', 'Album')
    albums = Album.objects.all()
    for album in albums:
        slides = []
        for member in album.albummembership_set.all():
            # single artworks are stored represented as a list with one id
            if not member.connected_with:
                slides.append([member.artwork.id])
            # connected artworks are represented as a list with two ids
            else:
                # in case nothing is in the slides yet, just add a first list
                if len(slides) == 0:
                    slides.append([member.artwork.id])
                else:
                    # check whether the current item is connected to the last one
                    if slides[-1][0] == member.connected_with.artwork.id:
                        # then add it to this sublist
                        slides[-1].append(member.artwork.id)
                    # otherwise just add a new list with one id
                    else:
                        slides.append([member.artwork.id])
        album.slides = slides
        album.save()


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0041_auto_20230406_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='slides',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Slides'),
        ),
        migrations.RunPython(code=create_slides_content, reverse_code=migrations.RunPython.noop),
    ]
