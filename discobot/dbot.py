import logging
import ctypes.util
import discord
from discord.ext import commands

from discobot.commands import DiscoBotCommands
from discobot.dbot_skills import DBotSkills

logger = logging.getLogger(__name__)


class DiscoBot(commands.Bot):

    def __init__(self, guild_name, **options):
        super().__init__(**options)
        self.guild_name = guild_name
        self.skills = DBotSkills()
        self.add_cog(DiscoBotCommands(self.skills))
        opus_lib = ctypes.util.find_library("opus")
        discord.opus.load_opus(opus_lib)
        if discord.opus.is_loaded():
            logger.info("Opus loaded successfully!")
        else:
            logger.error("I am unable to load Opus")

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

    async def on_ready(self):
        guild = discord.utils.find(lambda g: g.name == self.guild_name, self.guilds)
        if guild:
            logger.info("Guild found!")
            self.skills.guild = guild
        else:
            logger.warning("Guild not found. Voice might not work. Tried to find guild with name: {}"
                           "".format(self.guild_name))

    async def on_message(self, message):
        # don't respond to onw messages
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')
        else:
            await self.process_commands(message)

    async def close(self):
        if self.skills.guild.voice_client:
            await self.skills.guild.voice_client.disconnect()
        await super().close()
