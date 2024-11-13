# Generated by Django 4.2.16 on 2024-11-05 14:09

from django.db import migrations


def create_texts(apps, schema_editor):
    Text = apps.get_model("texts", "Text")
    for i, title in enumerate(['AGB / Terms of Service', 'Bildnutzung / Image Usage']):
        Text.objects.create(pk=i+1, title=title, de=title, en=title)

def delete_texts(apps, schema_editor):
    Text = apps.get_model("texts", "Text")
    Text.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('texts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=create_texts, reverse_code=delete_texts)
    ]
