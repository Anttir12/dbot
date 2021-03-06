# Generated by Django 3.1.6 on 2021-02-14 08:23
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('sounds', '0010_play_history'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favourites',
            options={'permissions': [('can_manage_own_favourites', 'Can manage own favourites')]},
        ),
        migrations.AlterModelOptions(
            name='soundeffect',
            options={'permissions': [('can_play_sound_with_bot', 'Can command bot to play sound'), ("can_download_sound", "Can download sound"), ('can_upload_clip_from_yt', 'Can upload clip from YouTube')]},
        ),
    ]
