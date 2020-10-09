from django.db import models
from django.core.exceptions import ValidationError


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
    sound_effect = models.FileField(null=False, blank=False, upload_to="uploads/")
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
