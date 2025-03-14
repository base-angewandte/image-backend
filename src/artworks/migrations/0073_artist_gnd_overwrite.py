# Generated by Django 4.2.6 on 2024-06-25 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0072_alter_artist_synonyms'),
    ]

    operations = [
        migrations.AddField(
            model_name='artist',
            name='gnd_overwrite',
            field=models.BooleanField(default=True, help_text='Overwrite entry with data from GND?'),
        ),
    ]
