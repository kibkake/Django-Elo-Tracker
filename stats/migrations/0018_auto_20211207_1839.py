# Generated by Django 3.2.8 on 2021-12-07 18:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stats', '0017_auto_20211207_0747'),
    ]

    operations = [
        migrations.RenameField(
            model_name='upcoming',
            old_name='date',
            new_name='game_date',
        ),
        migrations.RemoveField(
            model_name='match',
            name='participant_A',
        ),
        migrations.RemoveField(
            model_name='match',
            name='participant_B',
        ),
        migrations.RemoveField(
            model_name='upcoming',
            name='participant_A',
        ),
        migrations.RemoveField(
            model_name='upcoming',
            name='participant_B',
        ),
        migrations.AddField(
            model_name='match',
            name='player_A',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participant_A', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='match',
            name='player_B',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participant_B', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='upcoming',
            name='player_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='player_1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='upcoming',
            name='player_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='player_2', to=settings.AUTH_USER_MODEL),
        ),
    ]
