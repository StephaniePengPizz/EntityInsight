# Generated by Django 5.1.3 on 2025-03-17 06:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('text_classification', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship_type', models.CharField(max_length=100)),
                ('entity1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity1', to='knowledge_graph.entity')),
                ('entity2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity2', to='knowledge_graph.entity')),
                ('source_article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='text_classification.newsarticle')),
            ],
        ),
    ]
