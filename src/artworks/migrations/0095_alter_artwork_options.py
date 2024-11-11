from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0094_alter_artwork_image_paths'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='artwork',
            options={'managed': False},
        ),
    ]
