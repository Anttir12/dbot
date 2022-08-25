# Generated by Django 3.2.14 on 2022-07-30 16:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sounds', '0016_mention_to_user_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventtriggeredsoundeffect',
            options={'permissions': [('can_trigger_discord_event', 'Can trigger discord events')]},
        ),
        migrations.AlterModelOptions(
            name='soundeffect',
            options={'permissions': [('can_play_sound_with_bot', 'Can command bot to play sound'), ('can_download_sound', 'Can download sound'), ('can_upload_clip_from_yt', 'Can upload clip from YouTube'), ('can_play_yt', 'Can play sounds directly from yt')]},
        ),
    ]
