import asyncio
import json
import logging
import random
import redis

from asgiref.sync import sync_to_async
from django.utils import timezone

from sounds import utils, models

logger = logging.getLogger(__name__)


r = redis.StrictRedis(host="localhost", port=6379, db=7, decode_responses=True)
SOUND_QUEUE = "SOUND_QUEUE"
DEFAULT_VOLUME = "DEFAULT_VOLUME"
MAX_QUEUE_LENGTH = 5
BOT_STATUS = "BOT_STATUS"
SOUND_OVERRIDE = "SOUND_OVERRIDE"


class SkillException(Exception):
    pass


async def play_sound(sound_effect: models.SoundEffect, override=False):
    if override:
        return play_sound_now(sound_effect)

    added_to_queue = add_to_queue_and_play(sound_effect)
    return added_to_queue


async def play_from_yt_url(yt_url: str, volume=None):
    cached_stream: models.CachedStream = await sync_to_async(utils.get_stream)(yt_url)
    if cached_stream:
        return add_to_queue_and_play(cached_stream, volume)

    logger.info("Could not find stream")
    raise SkillException("Unable to find stream")


async def welcome_user_voice(user_id: str):
    event_sounds = await sync_to_async(list)(models.EventTriggeredSoundEffect.objects.filter(
        event=models.WELCOME, discord_user__user_id=user_id).select_related("sound_effect"))
    if not event_sounds:
        event_sounds = await sync_to_async(list)(models.EventTriggeredSoundEffect.objects.filter(
            event=models.WELCOME, discord_user__isnull=True).select_related("sound_effect"))
    if event_sounds:
        event = random.choice(event_sounds)
        play_only_if_not_playing(event.sound_effect)


async def greetings_joining_voice():
    event_sounds = await sync_to_async(list)(models.EventTriggeredSoundEffect.objects.filter(event=models.GREETINGS)
                                             .select_related("sound_effect"))
    if event_sounds:
        event = random.choice(event_sounds)
        for _ in range(5):
            await asyncio.sleep(0.5)

        play_only_if_not_playing(event.sound_effect)


async def ow_event(hero: models.OwEventSoundEffect.Hero, event: models.OwEventSoundEffect.Event,
                   team: models.OwEventSoundEffect.Team, override: bool = True):

    ow_events = await sync_to_async(list)(models.OwEventSoundEffect.objects.filter(
        hero=hero, event=event, team=team).select_related("sound_effect"))
    if not ow_events:
        ow_events = await sync_to_async(list)(models.OwEventSoundEffect.objects.filter(
            event=event, team=team).select_related("sound_effect"))
    if ow_events:
        event = random.choice(ow_events)
        logger.info(f"Playing {event.file} which was triggered by ow_event {event} {team} {hero}")
        if override:
            play_sound_now(event.sound_effect)
        else:
            play_only_if_not_playing(event.sound_effect)
    else:
        logger.info(f"No action set for event {event} {team}")


def add_to_queue_and_play(sound: models.Playable, volume=None):
    added_to_queue = add_sound_to_queue(sound, volume)
    return added_to_queue


def add_sound_to_queue(sound: models.Playable, volume=None):
    if not volume:
        volume = r.get(DEFAULT_VOLUME)

    queue_length = r.llen(SOUND_QUEUE)
    if queue_length < MAX_QUEUE_LENGTH:
        sound_json = _create_sound_json(sound, volume)
        r.rpush(SOUND_QUEUE, sound_json)
        return True

    logger.info("Queue full")
    return False


def play_sound_now(sound: models.Playable, volume=None):
    sound_json = _create_sound_json(sound, volume)
    r.set(SOUND_OVERRIDE, sound_json)


def play_only_if_not_playing(sound: models.Playable, volume=None):
    if r.get(BOT_STATUS) == "idle" and r.llen(SOUND_QUEUE) == 0:
        return add_sound_to_queue(sound, volume)

    return False


def clear_queue():
    r.delete(SOUND_QUEUE)


def _create_sound_json(sound: models.Playable, volume):
    return json.dumps({
            "path": sound.file.path,
            "name": sound.name,
            "volume": volume,
            "timestamp": timezone.now().isoformat()
        })
