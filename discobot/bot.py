import asyncio
import logging
import os
import threading
from time import sleep
from typing import Optional

from django.conf import settings

from discobot.dbot import DiscoBot


logger = logging.getLogger(__name__)


# TODO this weird bot thing needs to be reworked
class Bot:  # pylint: disable=too-few-public-methods
    bot: Optional[DiscoBot] = None
    disco_bot_loop = None
    disco_bot_thread = None

    @staticmethod
    def init():
        init_bot()


def init_bot():
    logger.info("Initialising bot")
    Bot.disco_bot_loop = asyncio.get_event_loop()
    Bot.disco_bot_loop.create_task(start_bot(Bot))
    Bot.disco_bot_thread = threading.Thread(target=Bot.disco_bot_loop.run_forever)
    Bot.disco_bot_thread.start()
    pid = os.getpid()
    while not Bot.bot or not Bot.bot.is_ready():
        if not Bot.bot:
            logger.info("Bot is None")
        if Bot.bot and not Bot.bot.is_ready():
            logger.info("Bot is not ready!")
        logger.info("Waiting for bot to get ready  PID:{}".format(pid))
        sleep(0.5)
    logger.info("BOT IS INITIALISED!!")


async def start_bot(bot_wrapper):
    pid = os.getpid()
    logger.info("Started bot! and test ok? PID:{}".format(pid))
    bot_wrapper.bot = DiscoBot(settings.DISCORD_GUILD, command_prefix=settings.COMMAND_PREFIX)
    await bot_wrapper.bot.start(settings.DISCORD_TOKEN)
