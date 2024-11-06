# Generated by Django 4.2.16 on 2024-10-18 12:41
import logging

from django.db import migrations, models


logger = logging.getLogger(__name__)

def update_search_vector(apps, schema_editor):
    from artworks.models import Artwork

    for artwork in Artwork.objects.all():
        if hasattr(artwork, 'update_search_vector') and callable(artwork.update_search_vector):
            artwork.update_search_vector()
        else:
            logger.warning('Artwork model does not have a update_search_vector method')
            break


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0089_rename_synonyms_location_synonyms_old_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='search_keywords',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='artwork',
            name='search_locations',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='artwork',
            name='search_materials',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='artwork',
            name='search_persons',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.RunPython(update_search_vector, reverse_code=migrations.RunPython.noop),
    ]
