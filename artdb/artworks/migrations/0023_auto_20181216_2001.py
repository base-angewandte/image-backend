# Generated by Django 2.0.6 on 2018-12-16 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0022_auto_20181216_1956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='synonyms',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
