# Generated by Django 5.1.3 on 2025-04-24 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsarticle',
            name='title',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]
