import shutil

import pytube
import logging

from asgiref.sync import sync_to_async
from discord import FFmpegPCMAudio, Guild, PCMVolumeTransformer
from discord.abc import GuildChannel
from discord.ext.commands import Context
from django.db.models import Q

from sounds import utils
from sounds.models import SoundEffect

logger = logging.getLogger(__name__)


class SkillException(Exception):
    pass


class DBotSkills:

    def __init__(self):
        self.guild: Optional[Guild] = None
        self.channel = None
        self.volume = 0.75

    async def play_sound(self, sound: Union[str, SoundEffect], channel: Optional[GuildChannel],
                         override=False, gif=True):
        logger.info("Playing sound")
        voice_client = self.guild.voice_client
        if not voice_client:
            logger.info("Voice client not found!")
            return
        if voice_client.is_playing():
            if override:
                voice_client.stop()
            else:
                logger.info("already playing something. Skipping this")
                return
        if isinstance(sound, str):
            logger.info("Finding sound effect with name: {}".format(sound))
            sound_effects = await sync_to_async(SoundEffect.objects.filter)(Q(name=sound) |
                                                                            Q(alternativename__name=sound))
            sound_effect = await sync_to_async(sound_effects.first)()
        else:
            logger.info("Sound was a soundeffect. No need to search")
            sound_effect = sound
        if not channel and self.channel:
            channel = self.channel
        if not sound_effect and channel:
            logger.info("Sound <{}> not found".format(sound))
            await channel.send("Sound <{}> not found".format(sound))
            return

        if voice_client:
            logger.info("voice_client found.")
            audio = PCMVolumeTransformer(FFmpegPCMAudio(sound_effect.sound_effect.path), self.volume)
            if gif and channel and await sync_to_async(sound_effect.gifs.exists)():
                gif = await sync_to_async(sound_effect.gifs.order_by("?").first)()
                await channel.send(gif.url)
            voice_client.play(audio)
        else:
            logger.info("voice_client NOT found")

    async def play(self, yt_url: str):
        if not yt_url.startswith("https://www.youtube.com/") and not yt_url.startswith("https://youtu.be/"):
            raise SkillException("URL not valid. URL has to start with <https://www.youtube.com/> or "
                                 "<https://youtu.be/>")
        try:
            y_t = pytube.YouTube(yt_url)
        except Exception as broad_except:  # pylint: disable=broad-except
            raise SkillException("Unable to load streams from {}".format(yt_url)) from broad_except
        filtered = y_t.streams.filter(audio_codec="opus").order_by('bitrate').desc().first()
        if not utils.enough_disk_space_for_yt_stream(filtered, "/tmp"):
            raise SkillException("Not enough disk space to download yt stream")
        download = filtered.download("/tmp/streams")
        if filtered:
            if self.guild.voice_client:
                if self.channel:
                    self.channel.send("Now playing {}".format(filtered.title))
                audio = PCMVolumeTransformer(FFmpegPCMAudio(download), self.volume)
                self.guild.voice_client.play(audio)
        elif self.channel:
            await self.channel.send("I was unable to find a proper stream. Sorry!")

    async def set_channel(self, ctx: Context):
        cid = ctx.message.channel.id
        self.channel = ctx.message.channel
        await ctx.message.channel.send(f"Channel ID: {cid}")
