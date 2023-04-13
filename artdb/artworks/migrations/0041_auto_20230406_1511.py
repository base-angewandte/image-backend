# Generated by Django 2.2.1 on 2023-04-06 13:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artworks', '0040_auto_20210329_1139'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
            ],
            options={
                'verbose_name': 'Folder',
                'verbose_name_plural': 'Folders',
                'permissions': (('can_download_pptx', 'Can download as PowerPoint file'),),
            },
        ),
        migrations.RenameModel(
            old_name='ArtworkCollectionMembership',
            new_name='AlbumMembership',
        ),
        migrations.AlterField(
            model_name='albummembership',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artworks.Album', verbose_name='Folder'),
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
        migrations.DeleteModel(
            name='ArtworkCollection',
        ),
        migrations.AddField(
            model_name='album',
            name='artworks',
            field=models.ManyToManyField(through='artworks.AlbumMembership', to='artworks.Artwork', verbose_name='Artworks'),
        ),
        migrations.AddField(
            model_name='album',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
