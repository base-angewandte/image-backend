# Generated by Django 2.2.28 on 2023-08-28 13:48

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artworks', '0043_album_shared_info'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'permissions': (('can_download_pptx', 'Can download as PowerPoint file'),), 'verbose_name': 'Album', 'verbose_name_plural': 'Albums'},
        ),
        migrations.RemoveField(
            model_name='album',
            name='shared_info',
        ),
        migrations.AddField(
            model_name='album',
            name='permissions',
            field=models.ManyToManyField(related_name='permissions_album', to=settings.AUTH_USER_MODEL, verbose_name='Permissions'),
        ),
        migrations.AlterField(
            model_name='keyword',
            name='level',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='keyword',
            name='lft',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='keyword',
            name='rght',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='location',
            name='level',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='location',
            name='lft',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='location',
            name='rght',
            field=models.PositiveIntegerField(editable=False),
        ),
    ]
