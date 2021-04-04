from bot.dbot import DiscoBot
from bot.dbot_skills import DBotSkills


class DiscoMockBot(DiscoBot):

    def __init__(self):  # This is just for mocking purposes  pylint: disable=super-init-not-called
        self.skills = DBotSkills(None)
