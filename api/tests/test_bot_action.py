import os
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse

from api.tests.test import DbotApiTest
from bot.dbot_skills import DBotSkills
from sounds.models import SoundEffect


class BotActionTest(DbotApiTest):

    def setUp(self):
        bot_users = Group.objects.get(name="Bot user")
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")
        bot_users.user_set.add(self.user1)
        path = os.path.join(settings.TEST_DATA, "nerd.ogg")
        with open(path, "rb") as audio:
            size = os.path.getsize(path)
            file = InMemoryUploadedFile(audio, "sound_effect", audio.name, None, size, None)
            self.se1 = SoundEffect.objects.create(name="sound_effect_1", sound_effect=file, created_by=self.user1)

    def test_play_sound(self):
        self._set_jwt_credentials(self.user1.username)
        with patch.object(DBotSkills, "play_sound") as play_sound:
            response = self.client.post(reverse("api:play_sound"), data={"sound_effect_id": self.se1.id,
                                                                         "override": False})
            self.assertEqual(response.json(), {"bot": "ok"})
            play_sound.assert_called_once()
