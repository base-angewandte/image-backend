# Generated by Django 2.0.6 on 2019-03-21 12:54

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0037_auto_20190312_1049'),
    ]

    operations = [
        UnaccentExtension(),
    ]
