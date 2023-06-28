from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_albums(apps, schema_editor):
    """Copies all data from the artworkcollection table to the (new) album table"""
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('INSERT INTO artworks_album SELECT * FROM artworks_artworkcollection')


def copy_albums_reverse(apps, schema_editor):
    """Deletes all rows on the album table"""
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('TRUNCATE artworks_album')


def copy_artworkcollection(apps, schema_editor):
    """Copies (back) all data from the album table to the (old) artworkcollection table"""
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('INSERT INTO artworks_artworkcollection SELECT * FROM artworks_album')


def noop(apps, schema_editor):
    """Placeholder for an empty operation"""
    pass


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
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Folder',
                'verbose_name_plural': 'Folders',
                'permissions': (('can_download_pptx', 'Can download as PowerPoint file'),),
            },
        ),
        migrations.RunPython(code=copy_albums, reverse_code=copy_albums_reverse),
        migrations.AlterField(
            model_name='artworkcollectionmembership',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artworks.Album',
                                    verbose_name='Folder'),
        ),
        # before the previous migration can be reversed, we need to copy back all album
        # data into the artworkcollection table, otherwise the foreign key constraint will
        # raise an error
        migrations.RunPython(code=noop, reverse_code=copy_artworkcollection),
        migrations.RenameModel(
            old_name='ArtworkCollectionMembership',
            new_name='AlbumMembership',
        ),
        migrations.DeleteModel(
            name='ArtworkCollection',
        ),
        migrations.AddField(
            model_name='album',
            name='artworks',
            field=models.ManyToManyField(through='artworks.AlbumMembership', to='artworks.Artwork',
                                         verbose_name='Artworks'),
        ),
    ]
