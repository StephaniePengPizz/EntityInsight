# Generated by Django 5.1.3 on 2025-03-17 06:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('web_collection', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
                ('processed_content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('web_page', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='web_collection.webpage')),
            ],
        ),
    ]
