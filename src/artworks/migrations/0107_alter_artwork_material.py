# Generated by Django 4.2.16 on 2024-11-19 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0106_alter_artwork_keywords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artwork',
            name='material',
            field=models.ManyToManyField(related_name='artworks', to='artworks.material', verbose_name='Material/Technique'),
        ),
    ]
