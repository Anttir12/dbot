import asyncio

from asgiref.sync import sync_to_async
from celery.signals import worker_process_shutdown, worker_ready

from dbot.celery import app
from discobot.bot import Bot
from sounds.models import SoundEffect, OwEventSoundEffect


@worker_ready.connect
def at_startup(sender, **_):
    with sender.app.connection():
        sender.app.send_task("sounds.tasks.init_bot")


@worker_process_shutdown.connect
def shutdown(sender, **_):  # pylint: disable=unused-argument
    if Bot.bot and not Bot.bot.is_closed():
        asyncio.run_coroutine_threadsafe(Bot.bot.close(), Bot.disco_bot_loop)


@app.task
def init_bot():
    if not Bot.bot:
        Bot.init()


@app.task
def play_sound(sound_effect_id: int, override=False):
    sound_effect = asyncio.run(sync_to_async(SoundEffect.objects.get)(id=sound_effect_id))
    asyncio.run_coroutine_threadsafe(Bot.bot.skills.play_sound(sound_effect, None, override=override),
                                     Bot.disco_bot_loop)


@app.task
def trigger_ow_event(hero: OwEventSoundEffect.Hero, event: OwEventSoundEffect.Event, team: OwEventSoundEffect.Team,
                     override: bool = True):
    asyncio.run_coroutine_threadsafe(Bot.bot.skills.ow_event(hero, event, team, override), Bot.disco_bot_loop)
