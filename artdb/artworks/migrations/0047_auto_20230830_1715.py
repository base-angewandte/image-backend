# Generated by Django 2.2.28 on 2023-08-30 15:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0046_album_permissions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='permissionsrelation',
            old_name='relation',
            new_name='permissions',
        ),
    ]
