# Generated by Django 4.2.16 on 2024-11-13 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0102_alter_keyword_name_alter_location_synonyms_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='name',
            field=models.CharField(blank=True, max_length=255, unique=True, verbose_name='Name (DE)'),
        ),
    ]
