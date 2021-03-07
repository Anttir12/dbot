import logging
from typing import Optional

from asgiref.sync import sync_to_async
from discord.ext import commands
from discord.ext.commands import Context
from django.db.models import Q

from bot.dbot_skills import DBotSkills, SkillException
from sounds.models import SoundEffect

logger = logging.getLogger(__name__)


class DiscoBotCommands(commands.Cog):

    def __init__(self, skills: DBotSkills):
        super().__init__()
        self.skills: DBotSkills = skills

    @commands.command()
    @commands.guild_only()
    async def join(self, ctx: Context):
        if self.skills.guild.voice_client:
            await self.skills.guild.voice_client.disconnect()
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.message.channel.send("You are not in a voice channel")

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx: Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx: Context, yt_url: str, volume: Optional[float] = None):
        """
            Plays sound from youtube. Usage: !play <yt_url> <Optional volume (0-2)>
        """
        if volume:
            volume = float(volume)
        yt_url = clean_url(yt_url)
        try:
            await self.skills.play_from_yt_url(yt_url, volume)
        except SkillException as skill_exception:
            await ctx.message.channel.send(f"Error while trying to play from url: {yt_url}: {skill_exception}")

    @commands.command()
    @commands.guild_only()
    async def list_sounds(self, ctx: Context):
        name_query = await sync_to_async(SoundEffect.objects.values_list)("name", flat=True)
        name_query = await sync_to_async(name_query.order_by)("name")
        names = await sync_to_async(list)(name_query)
        await ctx.message.channel.send("Available sound effects:\n{}".format("\n".join(names)))

    @commands.command(name="!")
    @commands.guild_only()
    async def sound(self, ctx: Context, name):
        sound_effects = await sync_to_async(SoundEffect.objects.filter)(Q(name=name) |
                                                                        Q(alternativename__name=name))
        sound_effect = await sync_to_async(sound_effects.first)()
        await self.skills.play_sound(sound_effect, ctx.message.channel)

    @commands.command()
    @commands.guild_only()
    async def stop(self, ctx: Context):
        if ctx.voice_client:
            ctx.voice_client.stop()

    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()

    @commands.command()
    @commands.guild_only()
    async def resume(self, ctx: Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()

    @commands.command()
    @commands.guild_only()
    async def this_channel(self, ctx: Context, leave=False):
        if leave:
            self.skills.channel = None
        else:
            await self.skills.set_channel(ctx)

    @commands.command()
    @commands.guild_only()
    async def volume(self, ctx, volume: Optional[float] = None):
        if volume is None:
            await ctx.message.channel.send(f"Current volume is: {self.skills.volume}")
            return
        volume = float(volume)
        if not 0 <= volume <= 1:
            await ctx.message.channel.send("Volume has to be between 0 and 1")
            return
        self.skills.volume = volume


def clean_url(url: str):
    url = url.strip()
    if url:
        if url.startswith("<"):
            url = url[1:]
        if url.endswith(">"):
            url = url[0:-1]
    return url
