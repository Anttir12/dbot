from django.db import models

# Create your models here.
from sounds import models as sound_models


class SttReaction(models.Model):

    class ReactionType(models.TextChoices):
        PHRASE = "phrase", "Phrase - Reaction is triggered when the given phrase/word is detected in speech"
        REPEATS = "repeats", "Repeats - Reaction is triggered when given phrases/words have been repeated often " \
                             "enough in given timeframe"

    name = models.CharField(max_length=256)

    active = models.BooleanField(null=False,
                                 default=True,
                                 help_text="This reaction is not used if not active")
    cooldown = models.FloatField(null=False,
                                 default=5.0,
                                 help_text="How many seconds until this can be triggered again")
    data = models.JSONField(help_text="Format of this depends on the ReactionType", default={"any_phrase": []})
    sound_effects = models.ManyToManyField(sound_models.SoundEffect)

    def __str__(self):
        return f"{self.name} {'(inactive)' if not self.active else ''}"
