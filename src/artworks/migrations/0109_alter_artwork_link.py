# Generated by Django 4.2.16 on 2024-11-25 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0108_rename_material_artwork_materials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artwork',
            name='link',
            field=models.URLField(blank=True, verbose_name='Further information'),
        ),
    ]
