# Generated by Django 3.2.15 on 2022-08-17 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sounds', '0017_permissions'),
        ('stt', '0002_sttreaction_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='sttreaction',
            name='sound_effects',
            field=models.ManyToManyField(to='sounds.SoundEffect'),
        ),
    ]
