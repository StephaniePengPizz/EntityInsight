# Generated by Django 5.1.3 on 2025-04-07 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_relationship_source_article'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webpage',
            name='publication_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
