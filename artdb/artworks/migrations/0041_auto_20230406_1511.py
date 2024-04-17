from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artworks', '0040_auto_20210329_1139'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ArtworkCollection',
            new_name='Album'
        ),
        migrations.RenameModel(
            old_name='ArtworkCollectionMembership',
            new_name='AlbumMembership'
        ),
        migrations.AddField(
            model_name='album',
            name='artworks',
            field=models.ManyToManyField(through='artworks.AlbumMembership', to='artworks.Artwork',
                                         verbose_name='Artworks'),
        ),
    ]
