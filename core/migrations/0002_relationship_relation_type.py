# Generated by Django 5.1.3 on 2025-03-23 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationship',
            name='relation_type',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
