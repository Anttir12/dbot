# Generated by Django 3.2.14 on 2022-07-30 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sounds', '0015_playable_abstract_model'),
    ]

    operations = [
        migrations.RenameField(
            model_name='discorduser',
            old_name='mention',
            new_name='user_id',
        ),
    ]
