# Generated by Django 4.2.6 on 2024-06-14 11:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0069_artwork_title_comment'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='artwork',
            name='artworks_ar_search__9a85c2_gin',
        ),
    ]
