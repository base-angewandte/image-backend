# Generated by Django 4.2.6 on 2024-02-09 14:35

import artworks.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0049_trigram_extension'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permissionsrelation',
            name='permissions',
            field=models.CharField(choices=[('VIEW', 'VIEW'), ('EDIT', 'EDIT')], default=artworks.models.get_default_permissions, max_length=20),
        ),
    ]
