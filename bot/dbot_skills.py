import asyncio
import logging
import random
from typing import Optional

from asgiref.sync import sync_to_async
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
        self.volume = 0.8

    async def play_sound(self, sound_effect: SoundEffect, override=False):
        voice_client = self.guild.voice_client
        if not voice_client:
            logger.info("Voice client not found!")
            return False
        if voice_client.is_playing():
            if override:
                voice_client.stop()
            else:
                logger.info("already playing something. Skipping this")
                return False

        audio = PCMVolumeTransformer(FFmpegPCMAudio(sound_effect.sound_effect.path), self.volume)
        voice_client.play(audio)
        return True

    async def play_from_yt_url(self, yt_url: str):
        cached_stream = await sync_to_async(utils.get_stream)(yt_url)
        if cached_stream:
            source = cached_stream.file.path
            if self.guild.voice_client:
                if self.channel:
                    self.channel.send("Now playing {}".format(cached_stream.title))
                audio = PCMVolumeTransformer(FFmpegPCMAudio(source), self.volume)
                self.guild.voice_client.play(audio)
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
                await self.play_sound(event.sound_effect)

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
            await self.play_sound(event.sound_effect)

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
                await self.play_sound(event.sound_effect, override=override)
            else:
                logger.info(f"No action set for event {event} {team}")
        else:
            logger.info("Triggered event when no voice available")
