# Generated by Django 4.2.16 on 2024-11-19 15:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0107_alter_artwork_material'),
    ]

    operations = [
        migrations.RenameField(
            model_name='artwork',
            old_name='material',
            new_name='materials',
        ),
    ]
