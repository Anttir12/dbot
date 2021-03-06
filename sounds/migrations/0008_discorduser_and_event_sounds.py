# Generated by Django 3.1.4 on 2020-12-21 11:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_bot_user(apps, schema_editor):  # noqa
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username="bot").exists():
        User.objects.create(username="bot")


def do_nothing(apps, schema_editor):  # noqa
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sounds', '0007_sound_effect_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(max_length=255)),
                ('mention', models.CharField(max_length=255, unique=True)),
                ('auto_join', models.BooleanField(default=False)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_discord_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventTriggeredSoundEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(choices=[('welcome', 'Welcome'), ('greetings', 'Greetings')], max_length=255)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('discord_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sounds.discorduser')),
                ('sound_effect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sounds.soundeffect')),
            ],
        ),
        migrations.RunPython(create_bot_user, do_nothing),
    ]
