# Generated by Django 5.1.4 on 2024-12-26 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena_app', '0004_alter_quiz_dob_alter_quiz_gender_alter_quiz_location_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sessionid', models.IntegerField()),
                ('userid', models.IntegerField()),
            ],
        ),
    ]
