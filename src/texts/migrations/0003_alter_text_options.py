# Generated by Django 4.2.16 on 2024-11-06 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0002_auto_20241105_1509'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='text',
            options={'ordering': ('title',)},
        ),
    ]
