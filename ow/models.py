from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, UniqueConstraint

from sounds.models import SoundEffect


class Team(models.TextChoices):
    RED = "red"
    BLUE = "blue"


class Hero(models.Model):
    name = models.CharField(max_length=64, unique=True, null=False)

    def __str__(self):
        return self.name


class GameEvent(models.Model):
    name = models.CharField(max_length=64, unique=True, null=False)

    def __str__(self):
        return self.name


class EventReaction(models.Model):

    class Meta:
        constraints = [
            UniqueConstraint(fields=["event", "hero", "team"],
                             name='unique_with_optional'),
            UniqueConstraint(fields=["event", "team"],
                             condition=Q(hero=None),
                             name='unique_without_hero',
                             violation_error_message='Event reaction with this Event, Hero and Team already exists.'),
            UniqueConstraint(fields=["event", "hero"],
                             condition=Q(team=None),
                             name='unique_without_team',
                             violation_error_message='Event reaction with this Event, Hero and Team already exists.'),
            UniqueConstraint(fields=["event"],
                             condition=Q(team=None, hero=None),
                             name='unique_without_hero_and_team',
                             violation_error_message='Event reaction with this Event, Hero and Team already exists.'),
        ]
        unique_together = []

    event = models.ForeignKey(GameEvent, null=False, on_delete=models.PROTECT)
    hero = models.ForeignKey(Hero, null=True, blank=True, on_delete=models.PROTECT)
    team = models.CharField(max_length=64, null=True, blank=True, choices=Team.choices)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sound_effects = models.ManyToManyField(SoundEffect, null=True, blank=True)

    def __str__(self):
        team_str = f' by Team {self.team} ' if self.team else ''
        hero_str = f' {self.hero} ' if self.hero else ''
        return f'{self.event}{team_str}{hero_str}'
