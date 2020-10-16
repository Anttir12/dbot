import os
import logging
from typing import Optional, Union
from urllib.parse import urlparse, parse_qs

import magic
import pytube

from asgiref.sync import sync_to_async
from discord import FFmpegPCMAudio, Guild, PCMVolumeTransformer
from discord.abc import GuildChannel
from discord.ext.commands import Context
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q

from sounds import utils
from sounds.models import SoundEffect, CachedStream

logger = logging.getLogger(__name__)


class SkillException(Exception):
    pass


class DBotSkills:

    def __init__(self):
        self.guild: Optional[Guild] = None
        self.channel = None
        self.volume = 0.5

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
        source, title = await self._get_stream(yt_url)
        if source:
            if self.guild.voice_client:
                if self.channel:
                    self.channel.send("Now playing {}".format(title))
                audio = PCMVolumeTransformer(FFmpegPCMAudio(source), self.volume)
                self.guild.voice_client.play(audio)
            else:
                logger.info("Unable to find voice client")
        else:
            logger.info("No source: {}".format(source))
            if self.channel:
                await self.channel.send("I was unable to find a proper stream. Sorry!")

    async def set_channel(self, ctx: Context):
        cid = ctx.message.channel.id
        self.channel = ctx.message.channel
        await ctx.message.channel.send(f"Channel ID: {cid}")

    async def _get_stream(self, yt_url):
        yt_id = await self._get_yt_id_from_url(yt_url)
        cached_stream_query = await sync_to_async(CachedStream.objects.filter)(yt_id=yt_id)
        cached_stream: CachedStream = await sync_to_async(cached_stream_query.first)()
        if cached_stream:
            source = cached_stream.file.path
            title = cached_stream.title
            logger.info("{} found in cache. Skipping download".format(yt_id))
        else:
            source, title = await self._download_stream_and_cache_it(yt_url, yt_id)
        return source, title

    async def _download_stream_and_cache_it(self, yt_url, yt_id, cache_it=True):
        try:
            y_t = pytube.YouTube(yt_url)
        except Exception as broad_except:  # pylint: disable=broad-except
            raise SkillException("Unable to load streams from {}".format(yt_url)) from broad_except

        filtered = y_t.streams.filter(audio_codec="opus").order_by('bitrate').desc().first()
        if not utils.enough_disk_space_for_yt_stream(filtered, "/tmp"):
            raise SkillException("Not enough disk space to download yt stream")
        source = filtered.download("/tmp/streams")
        title = filtered.title
        size = os.path.getsize(source)
        if cache_it:
            with open(source, 'rb') as ytaudio:
                ytaudio.seek(0)
                mime_type = magic.from_buffer(ytaudio.read(1024), mime=True)
                ytaudio.seek(0)
                file = InMemoryUploadedFile(ytaudio, "sound_effect", title, mime_type, size, None)
                cached_stream = CachedStream(title=title, yt_id=yt_id, file=file, size=filtered.filesize_approx)
                await sync_to_async(cached_stream.save)(remove_oldest_if_full=True)
                temp_source = source
                source = cached_stream.file.path
                os.remove(temp_source)
        return source, title

    async def _get_yt_id_from_url(self, yt_url):
        parsed_url = urlparse(yt_url)
        if yt_url.startswith("https://www.youtube.com/"):
            yt_id = parse_qs(parsed_url.query)["v"][0]
        elif yt_url.startswith("https://youtu.be/"):
            yt_id = parsed_url.path[1:]
        else:
            raise SkillException("URL not valid. URL has to start with <https://www.youtube.com/> or "
                                 "<https://youtu.be/>")
        return yt_id
