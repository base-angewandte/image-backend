# Generated by Django 2.0.6 on 2018-10-16 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0005_keyword'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artwork',
            name='date',
            field=models.CharField(blank=True, help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende 14. Jh., 5.3.1799, um 1700', max_length=319),
        ),
    ]
