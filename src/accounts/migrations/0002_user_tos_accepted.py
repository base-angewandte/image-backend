# Generated by Django 4.2.14 on 2024-07-15 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='tos_accepted',
            field=models.BooleanField(default=False),
        ),
    ]
