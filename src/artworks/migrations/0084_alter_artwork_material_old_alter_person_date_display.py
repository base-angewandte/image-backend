# Generated by Django 4.2.15 on 2024-09-11 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0083_artwork_authors_artwork_graphic_designers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artwork',
            name='material_old',
            field=models.TextField(blank=True, default='', help_text='Deprecated. Used only if material is not chosen.', verbose_name='Material/Technique (old)'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='person',
            name='date_display',
            field=models.CharField(blank=True, default='', help_text='Overrides birth and death dates for display, if not empty.'),
            preserve_default=False,
        ),
    ]
