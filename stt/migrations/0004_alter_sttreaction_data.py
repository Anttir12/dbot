# Generated by Django 3.2.15 on 2022-08-20 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stt', '0003_sttreaction_sound_effects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sttreaction',
            name='data',
            field=models.JSONField(default={'any_phrase': []}, help_text='Format of this depends on the ReactionType'),
        ),
    ]