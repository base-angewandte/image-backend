# Generated by Django 4.2.6 on 2024-04-29 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0063_artwork_search_vector_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscriminatoryTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=255)),
            ],
        ),
    ]
