# Generated by Django 5.2.1 on 2025-05-21 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_movie_tmdb_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='tmdb_id',
            field=models.IntegerField(null=True, unique=True),
        ),
    ]
