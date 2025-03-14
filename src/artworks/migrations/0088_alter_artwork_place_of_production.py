# Generated by Django 4.2.16 on 2024-10-18 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0087_alter_artwork_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artwork',
            name='place_of_production',
            field=models.ManyToManyField(blank=True, related_name='artworks_created_here', to='artworks.location', verbose_name='Place of Production'),
        ),
    ]
