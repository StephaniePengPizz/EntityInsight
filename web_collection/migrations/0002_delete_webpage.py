# Generated by Django 5.1.3 on 2025-03-17 09:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('text_classification', '0002_delete_newsarticle'),
        ('web_collection', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WebPage',
        ),
    ]
