# Generated by Django 2.0.6 on 2019-02-05 22:11

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0031_auto_20190126_0746'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='location_current',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks_currently_located_here', to='artworks.Location'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='published',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='location_of_creation',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks_created_here', to='artworks.Location'),
        ),
    ]
