# Generated by Django 5.1.4 on 2024-12-25 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sessions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sport_type', models.CharField(max_length=100)),
                ('time', models.DateTimeField()),
                ('location', models.CharField(max_length=50)),
                ('game_size', models.IntegerField()),
                ('price', models.FloatField()),
                ('slots_taken', models.IntegerField()),
            ],
        ),
    ]
