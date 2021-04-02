import asyncio
import collections
import logging
import random
import threading
from time import sleep
from typing import Optional

from asgiref.sync import sync_to_async
from constance import config
from discord import FFmpegPCMAudio, Guild, PCMVolumeTransformer, VoiceClient
from discord.ext.commands import Context

from sounds import utils, models
from sounds.models import SoundEffect, EventTriggeredSoundEffect, OwEventSoundEffect

logger = logging.getLogger(__name__)


class SkillException(Exception):
    pass


class DBotSkills:

    def __init__(self):
        self.guild: Optional[Guild] = None
        self.channel = None
        self.default_volume = 0.8
        self.player = Player(voice_client=self.guild.voice_client if self.guild else None,
                             default_volume=self.default_volume)

    async def play_sound(self, sound_effect: SoundEffect, override=False):
        voice_client = self.guild.voice_client
        if not voice_client:
            logger.info("Voice client not found!")
            return False
        self.player.voice_client = self.guild.voice_client
        if override:
            return self.player.play_sound_now(sound_effect.sound_effect.path)

        added_to_queue = self.player.add_to_queue_and_play(sound_effect.sound_effect.path)
        return added_to_queue

    async def play_from_yt_url(self, yt_url: str, volume=None):
        cached_stream = await sync_to_async(utils.get_stream)(yt_url)
        if cached_stream:
            source = cached_stream.file.path
            if self.guild.voice_client:
                if self.channel:
                    self.channel.send("Now playing {}".format(cached_stream.title))
                self.player.play_sound_now(source, volume)
            else:
                logger.info("Unable to find voice client")
        else:
            logger.info("Could not find stream")
            if self.channel:
                await self.channel.send("I was unable to find a proper stream. Sorry!")

    async def set_channel(self, ctx: Context):
        cid = ctx.message.channel.id
        self.channel = ctx.message.channel
        await ctx.message.channel.send(f"Channel ID: {cid}")

    async def welcome_user_voice(self, member):
        voice_client = self.guild.voice_client
        if voice_client:
            event_sounds = await sync_to_async(list)(EventTriggeredSoundEffect.objects.filter(
                event=models.WELCOME, discord_user__mention=member.mention).select_related("sound_effect"))
            if not event_sounds:
                event_sounds = await sync_to_async(list)(EventTriggeredSoundEffect.objects.filter(
                    event=models.WELCOME, discord_user__isnull=True).select_related("sound_effect"))
            if event_sounds:
                event = random.choice(event_sounds)
                self.player.voice_client = self.guild.voice_client
                self.player.play_only_if_not_playing(event.sound_effect.sound_effect.path)

    async def greetings_joining_voice(self):
        event_sounds = await sync_to_async(list)(EventTriggeredSoundEffect.objects.filter(event=models.GREETINGS)
                                                 .select_related("sound_effect"))
        if event_sounds:
            event = random.choice(event_sounds)
            for _ in range(5):
                voice_client: VoiceClient = self.guild.voice_client
                if voice_client and voice_client.is_connected():
                    break
                await asyncio.sleep(0.5)
            self.player.voice_client = self.guild.voice_client
            self.player.play_only_if_not_playing(event.sound_effect.sound_effect.path)

    async def ow_event(self, hero: OwEventSoundEffect.Hero, event: OwEventSoundEffect.Event,
                       team: OwEventSoundEffect.Team, override: bool = True):
        voice_client = self.guild.voice_client
        if voice_client:
            ow_events = await sync_to_async(list)(OwEventSoundEffect.objects.filter(
                hero=hero, event=event, team=team).select_related("sound_effect"))
            if not ow_events:
                ow_events = await sync_to_async(list)(OwEventSoundEffect.objects.filter(
                    event=event, team=team).select_related("sound_effect"))
            if ow_events:
                event = random.choice(ow_events)
                logger.info(f"Playing {event.sound_effect} which was triggered by ow_event {event} {team} {hero}")
                self.player.voice_client = self.guild.voice_client
                if override:
                    self.player.play_sound_now(event.sound_effect.sound_effect.path)
                else:
                    self.player.play_only_if_not_playing(event.sound_effect.sound_effect.path)
            else:
                logger.info(f"No action set for event {event} {team}")
        else:
            logger.info("Triggered event when no voice available")

    def reinitialise_player(self):
        self.player = Player(voice_client=self.guild.voice_client if self.guild else None)

    def set_volume(self, volume):
        self.default_volume = volume
        self.player.volume = volume


class Player:

    def __init__(self, voice_client, default_volume=1.0):
        self.sound_queue_play_lock = threading.Lock()
        self.sound_deque = collections.deque(maxlen=config.MAX_QUEUE_SIZE)
        self.voice_client: VoiceClient = voice_client
        self.volume = default_volume

    def add_to_queue_and_play(self, path, volume=None):
        added_to_queue = self.add_sound_to_queue(path, volume)
        self.play_queue()
        return added_to_queue

    def add_sound_to_queue(self, path, volume=None):
        if not volume:
            volume = self.volume
        if len(self.sound_deque) < self.sound_deque.maxlen:
            self.sound_deque.append((path, volume))
            return True

        logger.info("Queue full")
        return False

    def play_sound_now(self, path, volume=None):
        if not volume:
            volume = self.volume
        if self.voice_client.is_playing():
            self.voice_client.stop()
        self.sound_deque.appendleft((path, volume))
        return self.play_queue()

    def play_only_if_not_playing(self, path, volume=None):
        if self.voice_client.is_playing():
            return False
        return self.play_sound_now(path, volume)

    def play_queue(self):
        if self.sound_queue_play_lock.acquire(blocking=True, timeout=0.5):

            def play():
                try:
                    while self.sound_deque:
                        if not self.voice_client:
                            logger.warning("Trying to play sound_queue without voice client. "
                                           "Clearing sound queue and returning...")
                            self.sound_deque.clear()
                            break

                        path, volume = self.sound_deque.popleft()
                        volume = 2 if volume > 2 else volume  # Make sure volume can't be over 2 to preserve hearing
                        audio = PCMVolumeTransformer(FFmpegPCMAudio(path), volume)
                        self.voice_client.play(audio)
                        while self.voice_client.is_playing():
                            sleep(0.1)
                finally:
                    self.sound_queue_play_lock.release()

            t = threading.Thread(target=play)
            t.start()
        else:
            return False
        return True
