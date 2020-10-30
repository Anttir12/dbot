# Generated by Django 3.1.2 on 2020-10-09 17:51

from django.db import migrations, models
import django.db.models.deletion
import sounds.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SoundEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_edited', models.DateTimeField(auto_now=True)),
                ('sound_effect', models.FileField(upload_to='uploads/soundeffects')),
                ('name', models.CharField(max_length=200, unique=True,
                                          validators=[sounds.models.validate_sound_effect_name])),
            ],
        ),
        migrations.CreateModel(
            name='SoundEffectGif',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=300)),
                ('sound_effect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gifs',
                                                   to='sounds.soundeffect')),
            ],
        ),
        migrations.CreateModel(
            name='AlternativeName',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True,
                                          validators=[sounds.models.validate_alternative_name])),
                ('sound_effect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                   to='sounds.soundeffect')),
            ],
        ),
    ]
