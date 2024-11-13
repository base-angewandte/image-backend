from django.db import migrations, models
import django.db.models.functions.text


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0065_rename_artwork_description_to_comments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='album',
            old_name='created_at',
            new_name='date_created',
        ),
        migrations.RenameField(
            model_name='album',
            old_name='updated_at',
            new_name='date_changed',
        ),
        migrations.AlterModelOptions(
            name='discriminatoryterm',
            options={'ordering': [django.db.models.functions.text.Upper('term')]},
        ),
        migrations.AlterField(
            model_name='album',
            name='date_changed',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='album',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='comments',
            field=models.TextField(blank=True, verbose_name='Comments'),
        ),
    ]
