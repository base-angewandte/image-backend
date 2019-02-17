# Generated by Django 2.0.6 on 2019-02-17 16:33

import artworks.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0034_artwork_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='artist',
            name='synonyms',
            field=models.CharField(blank=True, max_length=255, verbose_name='Synonyms'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='artists',
            field=models.ManyToManyField(blank=True, to='artworks.Artist', verbose_name='Artists'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='checked',
            field=models.BooleanField(default=False, verbose_name='Checked'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='credits',
            field=models.TextField(blank=True, verbose_name='Credits'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date',
            field=models.CharField(blank=True, help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700', max_length=319, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date_year_from',
            field=models.IntegerField(blank=True, null=True, verbose_name='Date From'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date_year_to',
            field=models.IntegerField(blank=True, null=True, verbose_name='Date To'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='description',
            field=models.TextField(blank=True, verbose_name='Descriptions'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='dimensions',
            field=models.CharField(blank=True, max_length=255, verbose_name='Dimensions'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='image_original',
            field=versatileimagefield.fields.VersatileImageField(blank=True, max_length=127, upload_to=artworks.models.get_path_to_original_file, verbose_name='Original Image'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='keywords',
            field=models.ManyToManyField(blank=True, to='artworks.Keyword', verbose_name='Artists'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='location_current',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks_currently_located_here', to='artworks.Location', verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='location_of_creation',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks_created_here', to='artworks.Location', verbose_name='Place of Production'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='material',
            field=models.TextField(blank=True, null=True, verbose_name='Material/Technique'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='published',
            field=models.BooleanField(default=False, verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='title',
            field=models.CharField(blank=True, max_length=255, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='title_english',
            field=models.CharField(blank=True, max_length=255, verbose_name='Title, English'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at'),
        ),
        migrations.AlterField(
            model_name='artworkcollection',
            name='artworks',
            field=models.ManyToManyField(through='artworks.ArtworkCollectionMembership', to='artworks.Artwork', verbose_name='Artworks'),
        ),
        migrations.AlterField(
            model_name='artworkcollection',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at'),
        ),
        migrations.AlterField(
            model_name='artworkcollection',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='artworkcollection',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated at'),
        ),
        migrations.AlterField(
            model_name='artworkcollection',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AlterField(
            model_name='artworkcollectionmembership',
            name='artwork',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artworks.Artwork', verbose_name='Artwork'),
        ),
        migrations.AlterField(
            model_name='artworkcollectionmembership',
            name='collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artworks.ArtworkCollection', verbose_name='Folder'),
        ),
        migrations.AlterField(
            model_name='keyword',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=255, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='location',
            name='synonyms',
            field=models.CharField(blank=True, max_length=255, verbose_name='Synonyms'),
        ),
    ]
