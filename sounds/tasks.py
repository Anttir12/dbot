import asyncio

from asgiref.sync import sync_to_async

from dbot.celery import app
from discobot.bot import Bot
from sounds.models import SoundEffect


@app.task
def play_sound(sound_effect_id: int, override=False):
    if not Bot.bot:
        Bot.init()
    sound_effect = asyncio.run(sync_to_async(SoundEffect.objects.get)(id=sound_effect_id))
    asyncio.run_coroutine_threadsafe(Bot.bot.skills.play_sound(sound_effect, None, override=override),
                                     Bot.disco_bot_loop)
