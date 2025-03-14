# Generated by Django 2.0.6 on 2018-12-16 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0020_auto_20181124_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='artist',
            name='synonyms',
            field=models.CharField(blank=True, max_length=255, verbose_name='synonyme'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='title',
            field=models.CharField(blank=True, max_length=255, verbose_name='title'),
        ),
    ]
