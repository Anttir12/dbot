import json
import os
from unittest.mock import patch

import libfaketime
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils import timezone

from api.tests import mocked_redis
from api.tests.test import DbotApiTest
from sounds.models import SoundEffect, EventTriggeredSoundEffect, WELCOME, DiscordUser
from bot.dbot_skills import SOUND_QUEUE, SOUND_OVERRIDE, BOT_STATUS
from ow import models as ow_models


@patch("bot.dbot_skills.r", mocked_redis.r)
class BotActionTest(DbotApiTest):

    def setUp(self):
        bot_users = Group.objects.get(name="Bot user")
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")
        bot_users.user_set.add(self.user1)
        discord_event_permission = Permission.objects.get(codename="can_trigger_discord_event")
        bot_users.permissions.add(discord_event_permission)
        path = os.path.join(settings.TEST_DATA, "nerd.ogg")
        with open(path, "rb") as audio:
            size = os.path.getsize(path)
            file1 = InMemoryUploadedFile(audio, "file", audio.name, None, size, None)
            file2 = InMemoryUploadedFile(audio, "file", audio.name, None, size, None)
            file3 = InMemoryUploadedFile(audio, "file", audio.name, None, size, None)
            self.se1 = SoundEffect.objects.create(name="sound_effect_1", file=file1, created_by=self.user1)
            self.se2 = SoundEffect.objects.create(name="sound_effect_2", file=file2, created_by=self.user1)
            self.se3 = SoundEffect.objects.create(name="sound_effect_3", file=file3, created_by=self.user1)

        EventTriggeredSoundEffect.objects.create(event=WELCOME, created_by=self.user1, sound_effect=self.se2)

        discord_user = DiscordUser.objects.create(display_name="Bot User", user_id="12345")
        EventTriggeredSoundEffect.objects.create(event=WELCOME, created_by=self.user1, sound_effect=self.se3,
                                                 discord_user=discord_user)

        self._set_jwt_credentials(self.user1.username)

    def test_play_sound(self):
        now = timezone.now()
        with libfaketime.freeze_time(now):
            response = self.client.post(reverse("api:play_sound"), data={"sound_effect_id": self.se1.id,
                                                                         "override": False})
        self.assertEqual(1, mocked_redis.r.llen(SOUND_QUEUE))
        sound_json = mocked_redis.r.lpop(SOUND_QUEUE)
        sound_dict = json.loads(sound_json)

        self.assertEqual(sound_dict, {
            "path": self.se1.file.path,
            "name": self.se1.name,
            "volume": None,
            "timestamp": now.isoformat()
        })
        self.assertEqual(response.json(), {"bot": "ok"})

    def test_play_sound_override(self):
        now = timezone.now()
        with libfaketime.freeze_time(now):
            response = self.client.post(reverse("api:play_sound"), data={"sound_effect_id": self.se1.id,
                                                                         "override": True})
        self.assertEqual(0, mocked_redis.r.llen(SOUND_QUEUE))
        sound_json = mocked_redis.r.get(SOUND_OVERRIDE)
        sound_dict = json.loads(sound_json)

        self.assertEqual(sound_dict, {
            "path": self.se1.file.path,
            "name": self.se1.name,
            "volume": None,
            "timestamp": now.isoformat()
        })
        self.assertEqual(response.json(), {"bot": "ok"})

    def test_discord_event_welcome(self):
        mocked_redis.r.set(BOT_STATUS, "idle")
        now = timezone.now()
        with libfaketime.freeze_time(now):
            response = self.client.post(reverse("api:discord_event_welcome"), data={"user_id": "32132"})
            self.assertEqual(201, response.status_code, response.content)
        self.assertEqual(1, mocked_redis.r.llen(SOUND_QUEUE))
        sound_json = mocked_redis.r.lpop(SOUND_QUEUE)
        sound_dict = json.loads(sound_json)

        self.assertEqual(sound_dict, {
            "path": self.se2.file.path,
            "name": self.se2.name,
            "volume": None,
            "timestamp": now.isoformat()
        })
        self.assertEqual(response.json(), {"bot": "ok"})

    def test_discord_event_welcome_with_user(self):
        now = timezone.now()
        mocked_redis.r.set(BOT_STATUS, "idle")
        with libfaketime.freeze_time(now):
            response = self.client.post(reverse("api:discord_event_welcome"), data={"user_id": "12345"})
        self.assertEqual(1, mocked_redis.r.llen(SOUND_QUEUE))
        sound_json = mocked_redis.r.lpop(SOUND_QUEUE)
        sound_dict = json.loads(sound_json)

        self.assertEqual(sound_dict, {
            "path": self.se3.file.path,
            "name": self.se3.name,
            "volume": None,
            "timestamp": now.isoformat()
        })
        self.assertEqual(response.json(), {"bot": "ok"})

    def test_ow_event_with_hero_without_event_with_hero(self):
        hero_name = "Ana"
        event_name = "double_kill"
        team = ow_models.Team.BLUE
        reaction: ow_models.EventReaction = ow_models.EventReaction.objects.get(event__name=event_name, team=team.value)
        reaction.sound_effects.add(self.se1)
        response = self.client.post(reverse("api:ow_event"),
                                    data={"hero": hero_name, "event": event_name, "team": team})
        self.assertTrue(200 <= response.status_code < 300)
        self.assertEqual({"event_triggered": True}, response.json())

    def test_ow_event_missing_hero(self):
        event_name = "double_kill"
        team = ow_models.Team.BLUE
        reaction: ow_models.EventReaction = ow_models.EventReaction.objects.get(event__name=event_name, team=team.value)
        reaction.sound_effects.add(self.se1)
        response = self.client.post(reverse("api:ow_event"), data={"event": event_name, "team": team})
        self.assertTrue(200 <= response.status_code < 300)
        self.assertEqual({"event_triggered": True}, response.json())

    def test_ow_event_blank_hero(self):
        event_name = "double_kill"
        team = ow_models.Team.BLUE
        reaction: ow_models.EventReaction = ow_models.EventReaction.objects.get(event__name=event_name, team=team.value)
        reaction.sound_effects.add(self.se1)
        response = self.client.post(reverse("api:ow_event"), data={"hero": "", "event": event_name, "team": team})
        self.assertTrue(200 <= response.status_code < 300)
        self.assertEqual({"event_triggered": True}, response.json())
