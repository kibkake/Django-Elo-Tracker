# Generated by Django 3.2.7 on 2021-11-19 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_auto_20211119_0109'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='image',
            field=models.ImageField(default='game_default.jpg', upload_to='game_pics'),
        ),
    ]
