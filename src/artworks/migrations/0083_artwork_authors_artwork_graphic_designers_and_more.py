# Generated by Django 4.2.15 on 2024-08-23 05:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0082_alter_location_gnd_id_alter_person_gnd_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='authors',
            field=models.ManyToManyField(related_name='authors', to='artworks.person', verbose_name='Authors'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='graphic_designers',
            field=models.ManyToManyField(related_name='graphic_designers', to='artworks.person', verbose_name='Graphic designers'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='photographers',
            field=models.ManyToManyField(related_name='photographers', to='artworks.person', verbose_name='Photographers'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='link',
            field=models.URLField(blank=True, verbose_name='Link'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='credits_link',
            field=models.URLField(blank=True, verbose_name='Credits URL'),
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_changed', models.DateTimeField(auto_now=True)),
                ('name', models.TextField(verbose_name='Material/Technique')),
                ('name_en', models.TextField(blank=True, default='', verbose_name='Material/Technique, English')),
            ],
            options={
                'ordering': ('-date_created',),
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='artwork',
            old_name='material',
            new_name='material_old',
        ),
        migrations.AlterField(
            model_name='artwork',
            name='material_old',
            field=models.TextField(blank=True, help_text='Deprecated. Used only if material is not chosen.', null=True, verbose_name='Material/Technique (old)'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='material',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='artworks.material', verbose_name='Material/Technique'),
        ),
        migrations.RenameField(
            model_name='artwork',
            old_name='dimensions',
            new_name='dimensions_display',
        ),
        migrations.AlterField(
            model_name='artwork',
            name='dimensions_display',
            field=models.CharField(blank=True, help_text='Free text, can be used to overrule width x height x depth', max_length=255, verbose_name='Dimensions'),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='dimensions_display',
            field=models.CharField(blank=True, help_text='Generated from width, height, and depth, but can also be set manually.', max_length=255, verbose_name='Dimensions'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='depth',
            field=models.FloatField(blank=True, help_text='in cm', null=True, verbose_name='Depth'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='height',
            field=models.FloatField(blank=True, help_text='in cm', null=True, verbose_name='Height'),
        ),
        migrations.AddField(
            model_name='artwork',
            name='width',
            field=models.FloatField(blank=True, help_text='in cm', null=True, verbose_name='Width'),
        ),
    ]
