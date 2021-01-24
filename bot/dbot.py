import logging
import ctypes.util
from typing import Optional

import discord
from asgiref.sync import sync_to_async
from discord import Member, VoiceState, Guild, VoiceChannel
from discord.ext import commands
from django.contrib.auth.models import User

from bot import utils
from bot.commands import DiscoBotCommands
from bot.dbot_skills import DBotSkills
from sounds.models import DiscordUser

logger = logging.getLogger(__name__)


class DiscoBot(commands.Bot):

    def __init__(self, guild_name, **options):
        super().__init__(**options)
        self.guild_name = guild_name
        self.guild: Optional[Guild] = None
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
        guild: Guild = discord.utils.find(lambda g: g.name == self.guild_name, self.guilds)
        if guild:
            logger.info("Guild found!")
            self.skills.guild = guild
            self.guild = guild
            await utils.run_task_with_delay(2, self.update_discord_user_table())
        else:
            logger.warning("Guild not found. Voice might not work. Tried to find guild with name: {}"
                           "".format(self.guild_name))

    async def update_discord_user_table(self):
        # TODO: Update display name. Also this could be done more efficiently, but I don't really care
        self.guild.fetch_members(limit=None, after=None)
        saved_users = await sync_to_async(list)(DiscordUser.objects.all())
        bot_user = await sync_to_async(User.objects.get)(username="bot")
        current_users = [DiscordUser(display_name=m.display_name, mention=m.mention, added_by=bot_user)
                         for m in self.guild.members if m != self.user]
        for saved_user in saved_users:
            if not any([True for user in current_users if user.mention == saved_user.mention]):
                await sync_to_async(saved_user.delete)()  # Delete saved DiscordUser (not found in guild anymore)
        for user in current_users:
            if not any([True for saved_user in saved_users if user.mention == saved_user.mention]):
                await sync_to_async(user.save)()  # create new DiscordUser

    async def on_message(self, message):
        # don't respond to own messages
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')
        else:
            await self.process_commands(message)

    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        voice_client = self.guild.voice_client if self.guild else None
        bots_channel = voice_client.channel if voice_client else None
        if member != self.user:
            # User joined some channel
            if after.channel and before.channel != after.channel:
                # User joined bot's current channel
                if voice_client and bots_channel == after.channel:
                    await utils.run_task_with_delay(0.7, self.skills.welcome_user_voice(member))
                # Bot is not in voice or is alone in another channel and user expects bot to follow
                elif await self.auto_join_condition_met(member):
                    await utils.run_task_with_delay(1, self.join_voice_channel(after.channel))
                # User left bot's channel and bot is alone
                elif voice_client and before.channel == bots_channel and len(bots_channel.members) == 1:
                    await utils.run_task_with_delay(5, self.check_if_we_should_leave_voice())
            # User left voice completely
            elif not after.channel and before.channel:
                if bots_channel and len(bots_channel.members) == 1:
                    await utils.run_task_with_delay(5, self.check_if_we_should_leave_voice())
        else:
            # Bot itself just joined to channel
            if before.channel != after.channel and voice_client:
                await utils.run_task_with_delay(0.5, self.skills.greetings_joining_voice())

    async def auto_join_condition_met(self, member):
        voice_client = self.guild.voice_client if self.guild else None
        # Bot is not in voice or is alone in a voice channel
        bot_ok_to_join = (not voice_client or not voice_client.channel or len(voice_client.channel.members) == 1)
        expects = False
        if bot_ok_to_join:
            expects = await sync_to_async(DiscordUser.objects.filter(mention=member.mention, auto_join=True).exists)()
        return expects

    async def close(self):
        if self.skills.guild.voice_client:
            await self.skills.guild.voice_client.disconnect()
        await super().close()

    async def join_voice_channel(self, channel: VoiceChannel):
        voice_client = self.guild.voice_client if self.guild else None
        if voice_client:
            await voice_client.disconnect()
        await channel.connect()

    async def check_if_we_should_leave_voice(self):
        voice_client = self.guild.voice_client if self.guild else None
        if voice_client and len(voice_client.channel.members) == 1:
            await voice_client.disconnect()
