# Generated by Django 2.0.6 on 2019-01-26 06:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0029_auto_20190126_0737'),
    ]

    operations = [
        migrations.RenameField(
            model_name='artwork',
            old_name='titleEnglish',
            new_name='title_english',
        ),
    ]
