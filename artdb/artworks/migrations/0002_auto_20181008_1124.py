# Generated by Django 2.1 on 2018-10-08 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='dateFromYear',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='artwork',
            name='dateToYear',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
