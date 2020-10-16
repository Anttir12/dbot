import logging

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_alternative_name(name):
    if SoundEffect.objects.filter(name=name).exists():
        raise ValidationError(f"{name} must not exist in SoundEffect")


def validate_sound_effect_name(name):
    if AlternativeName.objects.filter(name=name).exists():
        raise ValidationError(f"{name} must not exist in AlternativeNames")


class SoundEffect(models.Model):
    objects = models.Manager()  # Not needed but only paid pycharm detects this without this :D
    created_at = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    sound_effect = models.FileField(null=False, blank=False, upload_to="uploads/soundeffects/")
    name = models.CharField(null=False, blank=False, max_length=200, unique=True,
                            validators=[validate_sound_effect_name])

    def __str__(self):
        return self.name


class SoundEffectGif(models.Model):
    objects = models.Manager()  # Not needed but only paid pycharm detects this without this :D
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE, related_name="gifs")
    url = models.CharField(max_length=300)


class AlternativeName(models.Model):
    objects = models.Manager()  # Not needed but only paid pycharm detects this without this :D
    sound_effect = models.ForeignKey(SoundEffect, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True, validators=[validate_alternative_name])


class CachedStream(models.Model):
    objects = models.Manager()
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
