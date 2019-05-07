# Generated by Django 2.0.6 on 2019-02-16 16:22

from django.db import migrations, models
import django.db.models.functions


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0032_auto_20190205_2311'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='artwork',
            options={'ordering': [django.db.models.functions.Upper('title')]},
        ),
        migrations.AlterField(
            model_name='artwork',
            name='date',
            field=models.CharField(blank=True, help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700', max_length=319),
        ),
    ]
