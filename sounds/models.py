import logging

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


def validate_alternative_name(name):
    if SoundEffect.objects.filter(name=name).exists():
        raise ValidationError(f"{name} must not exist in SoundEffect")


def validate_sound_effect_name(name):
    if AlternativeName.objects.filter(name=name).exists():
        raise ValidationError(f"{name} must not exist in AlternativeNames")


class Category(models.Model):
    name = models.CharField(max_length=128, unique=True, null=False)
    color_code = ColorField(null=False)
    text_color_code = ColorField(null=False, default="#000000")

    def __str__(self):
        return str(self.name)


class SoundEffect(models.Model):

    class Meta:
        permissions = [
            ("can_play_sound_with_bot", "Can command bot to play sound"),
            ("can_download_sound", "Can download sound"),
            ("can_upload_clip_from_yt", "Can upload clip from YouTube"),
        ]

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    last_edited = models.DateTimeField(auto_now=True)
    sound_effect = models.FileField(null=False, blank=False, upload_to="uploads/soundeffects/")
    name = models.CharField(null=False, blank=False, max_length=200, unique=True,
                            validators=[validate_sound_effect_name])
    categories = models.ManyToManyField(Category, blank=True, related_name="sound_effects")

    def __str__(self):
        return str(self.name)

    def clean_name(self):
        return str(self.name).replace("_", " ")


class SoundEffectGif(models.Model):
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE, related_name="gifs")
    url = models.CharField(max_length=300)


class AlternativeName(models.Model):
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True, validators=[validate_alternative_name])


class CachedStream(models.Model):
    yt_id = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=200, null=True)
    file = models.FileField(null=False, upload_to="uploads/cache/")
    size = models.IntegerField()  # Not yet used but probably useful for better control of the cache size

    def save(self, *args, remove_oldest_if_full=False, **kwargs):  # pylint: disable=arguments-differ
        cache_count = CachedStream.objects.count()
        if cache_count >= settings.MAX_CACHED_STREAMS and remove_oldest_if_full:
            oldest_cached = CachedStream.objects.all().order_by("id").first()
            logger.info("Deleting")
            oldest_cached.delete()
            cache_count -= 1
        if cache_count < settings.MAX_CACHED_STREAMS:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.file.path})"


class Favourites(models.Model):

    class Meta:
        Permission
        unique_together = [['owner', 'name']]
        permissions = [
            ("can_manage_own_favourites", "Can manage own favourites"),
        ]

    owner = models.ForeignKey(User, related_name="favourite_lists", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=False)
    sound_effects = models.ManyToManyField(to=SoundEffect, related_name="favourite_lists")

    def __str__(self):
        return f"{self.name}"


class DiscordUser(models.Model):
    display_name = models.CharField(max_length=255, null=False, blank=False)
    mention = models.CharField(max_length=255, null=False, blank=False, unique=True)
    added_by = models.ForeignKey(User, related_name="added_discord_users", on_delete=models.SET_NULL, null=True)
    auto_join = models.BooleanField(default=False)

    def __str__(self):
        return "{} ({})".format(self.display_name, self.mention)


WELCOME = "welcome"
GREETINGS = "greetings"

EVENT_TYPES = ((WELCOME, "Welcome"),
               (GREETINGS, "Greetings"))


class EventTriggeredSoundEffect(models.Model):

    event = models.CharField(choices=EVENT_TYPES, max_length=255, null=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE, null=False)
    discord_user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        end = "for user {}".format(self.discord_user.display_name) if self.discord_user else ""
        return "{} {}".format(self.event, end)


class OwEventSoundEffect(models.Model):

    class Event(models.TextChoices):
        DOUBLE_KILL = "double_kill"
        TRIPLE_KILL = "triple_kill"
        QUADRUPLE_KILL = "quadruple_kill"
        QUINTUPLE_KILL = "quintuple_kill"
        SEXTUPLE_KILL = "sextuple_kill"
        TEAM_KILL = "team_kill"

    class Team(models.TextChoices):
        RED = "red"
        BLUE = "blue"

    class Hero(models.TextChoices):
        ANA = "Ana"
        ASHE = "Ashe"
        BAPTISTE = "Baptiste"
        BASTION = "Bastion"
        BRIGITTE = "Brigitte"
        DOOMFIST = "Doomfist"
        DVA = "Dva"
        ECHO = "Echo"
        GENJI = "Genji"
        HANZO = "Hanzo"
        JUNKRAT = "Junkrat"
        LUCIO = "Lucio"
        MCREE = "Mcree"
        MEI = "Mei"
        MERCY = "Mercy"
        MOIRA = "Moira"
        ORISA = "Orisa"
        PHARAH = "Pharah"
        REAPER = "Reaper"
        REINHARDT = "Reinhardt"
        ROADHOG = "Roadhog"
        SIGMA = "Sigma"
        SOLDIER = "Soldier"
        SOMBRA = "Sombra"
        SYMMETRA = "Symmetra"
        TORBJORN = "Torbjorn"
        TRACER = "Tracer"
        WIDOWMAKER = "Widowmaker"
        WINSTON = "Winston"
        WRECKINGBALL = "Wreckingball"
        ZARYA = "Zarya"
        ZENYATTA = "Zenyatta"

    event = models.CharField(choices=Event.choices, max_length=64, null=False)
    hero = models.CharField(choices=Hero.choices, max_length=64, null=True, blank=True)
    team = models.CharField(choices=Team.choices, max_length=64, null=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return f'{self.event.replace("_", " ")} by team {self.team}'


class SoundEffectPlayHistory(models.Model):

    class Meta:
        # Not sure about this (First join by sound_effect -> filter by played_by -> optionally filter by date)
        index_together = ["sound_effect", "played_by", "played_at"]

    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE, null=False, related_name="play_history")
    played_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    played_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_record(cls, sound_effect, played_by):
        record_limit_per_user = timezone.now() - timezone.timedelta(seconds=1)
        record_limit_per_user_per_sound = timezone.now() - timezone.timedelta(seconds=5)
        # plays from same user within one second or same user and same sound within 5 seconds are not counted
        if not SoundEffectPlayHistory.objects.filter(
                Q(played_by=played_by, played_at__gte=record_limit_per_user) |
                Q(played_by=played_by, sound_effect=sound_effect, played_at__gte=record_limit_per_user_per_sound)
        ).exists():
            SoundEffectPlayHistory.objects.create(sound_effect=sound_effect, played_by=played_by)

    def __str__(self):
        return "{} - {}".format(self.played_by.username, self.sound_effect)
