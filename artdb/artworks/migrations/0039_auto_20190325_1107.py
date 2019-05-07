# Generated by Django 2.0.6 on 2019-03-25 10:07

from django.db import migrations
import django.db.models.functions


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0038_auto_20190321_1354'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='artist',
            options={'ordering': ['name'], 'verbose_name': 'Artist', 'verbose_name_plural': 'Artists'},
        ),
        migrations.AlterModelOptions(
            name='artwork',
            options={'ordering': [django.db.models.functions.Upper('title')], 'verbose_name': 'Artwork', 'verbose_name_plural': 'Artworks'},
        ),
        migrations.AlterModelOptions(
            name='artworkcollection',
            options={'permissions': (('can_download_pptx', 'Can download as PowerPoint file'),), 'verbose_name': 'Folder', 'verbose_name_plural': 'Folders'},
        ),
        migrations.AlterModelOptions(
            name='keyword',
            options={'verbose_name': 'Keyword', 'verbose_name_plural': 'Keywords'},
        ),
        migrations.AlterModelOptions(
            name='location',
            options={'verbose_name': 'Location', 'verbose_name_plural': 'Locations'},
        ),
    ]
