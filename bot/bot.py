import asyncio
import logging
import os
import threading
from time import sleep
from typing import Optional

import discord
from django.conf import settings

from bot import mocks
from bot.dbot import DiscoBot


logger = logging.getLogger(__name__)

bot: Optional[DiscoBot] = None


def init_bot():
    logger.info("Initialising bot")
    disco_bot_loop = asyncio.new_event_loop()
    disco_bot_loop.create_task(start_bot())
    disco_bot_thread = threading.Thread(target=disco_bot_loop.run_forever)
    disco_bot_thread.start()
    pid = os.getpid()
    while not bot or not bot.is_ready():
        if not bot:
            logger.info("Bot is None")
        if bot and not bot.is_ready():
            logger.info("Bot is not ready!")
        logger.info("Waiting for bot to get ready  PID:{}".format(pid))
        sleep(0.5)


async def start_bot():
    pid = os.getpid()
    logger.info("Started bot! and test ok? PID:{}".format(pid))
    intents = discord.Intents.default()
    intents.members = True
    global bot  # Better solution needed. This works for now   pylint: disable=global-statement
    bot = DiscoBot(settings.DISCORD_GUILD, command_prefix=settings.COMMAND_PREFIX, intents=intents)
    await bot.start(settings.DISCORD_TOKEN)


def init_mock_bot():
    global bot  # Better solution needed. This works for now   pylint: disable=global-statement
    bot = mocks.DiscoMockBot()
