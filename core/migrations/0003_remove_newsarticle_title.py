# Generated by Django 5.1.3 on 2025-04-24 03:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_newsarticle_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsarticle',
            name='title',
        ),
    ]
