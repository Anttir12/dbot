import os

from django.apps import AppConfig
from django.conf import settings


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        from bot import bot  # pylint: disable=import-outside-toplevel
        if os.environ.get('RUN_MAIN', None) != 'true' and settings.RUN_BOT:
            bot.init_bot()
        elif getattr(settings, "USE_MOCK_BOT", False):
            bot.init_mock_bot()
