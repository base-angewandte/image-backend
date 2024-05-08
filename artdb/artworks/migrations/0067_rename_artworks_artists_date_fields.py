from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0066_rename_album_date_fields'),
    ]

    operations = [
        migrations.RunSQL('UPDATE artworks_artist SET updated_at = created_at WHERE updated_at IS NULL'),
        migrations.RunSQL('UPDATE artworks_artwork SET updated_at = created_at WHERE updated_at IS NULL'),
        migrations.RenameField(
            model_name='artist',
            old_name='created_at',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='artist',
            old_name='updated_at',
            new_name='date_changed',
        ),
        migrations.RenameField(
            model_name='artwork',
            old_name='created_at',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='artwork',
            old_name='updated_at',
            new_name='date_changed',
        ),
        migrations.AlterField(
            model_name='artist',
            name='date_changed',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date_changed',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
