# Generated by Django 4.2.13 on 2024-07-17 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0077_alter_location_synonyms'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='name_en',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Name_EN'),
        ),
    ]
