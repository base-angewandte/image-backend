# Generated by Django 4.2.15 on 2024-10-01 11:41

from django.db import migrations, models


def change_place_of_production_to_many(apps, schema_editor):
    """Migrate data from ForeignKey place_of_production to ManyToManyField place_of_production_new."""
    Artwork = apps.get_model('artworks', 'Artwork')

    for artwork in Artwork.objects.all():
        if artwork.place_of_production:
            # Migrate data from FK to M2M
            artwork.place_of_production_new.add(artwork.place_of_production)
            artwork.save()  # Ensure the changes are saved

def change_place_of_production_to_one(apps, schema_editor):
    """Migrate data from ManyToManyField place_of_production_new to ForeignKey place_of_production."""
    Artwork = apps.get_model('artworks', 'Artwork')
    for artwork in Artwork.objects.all():
        if artwork.place_of_production_new.count() > 0:
            # as there is no defined requirement, which location to take when
            # migrating back, we just take the first one the manager gives us
            artwork.place_of_production = artwork.place_of_production_new.all()[0]
            artwork.save(update_fields=['place_of_production'])

class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0084_alter_artwork_material_old_alter_person_date_display'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='place_of_production_new',
            field=models.ManyToManyField(
                related_name='artworks_created_here',
                to='artworks.location',
                verbose_name='Place of Production'
            ),
        ),

        migrations.RunPython(
            code=change_place_of_production_to_many,
            reverse_code=change_place_of_production_to_one
        ),

        migrations.RemoveField(
            model_name='artwork',
            name='place_of_production',
        ),

        migrations.RenameField(
            model_name='artwork',
            old_name='place_of_production_new',
            new_name='place_of_production',
        ),
    ]
