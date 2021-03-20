import os

import libfaketime
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from api.tests.test import DbotApiTest
from sounds.models import SoundEffect, Category


class SoundEffectTest(DbotApiTest):

    def setUp(self):
        bot_users = Group.objects.get(name="Bot user")
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")
        self.user2 = User.objects.create_user("User2", "test2@example.com", "x")
        bot_users.user_set.add(self.user1)
        bot_users.user_set.add(self.user2)
        self.category1 = Category.objects.create(name="category1", color_code="#000000", text_color_code="#123123")
        self.category2 = Category.objects.create(name="category2", color_code="#111111", text_color_code="#333333")
        path = os.path.join(settings.TEST_DATA, "nerd.ogg")
        with open(path, "rb") as audio:
            size = os.path.getsize(path)
            file = InMemoryUploadedFile(audio, "sound_effect", audio.name, None, size, None)
            now = timezone.now()
            self.created_at_drf = serializers.DateTimeField().to_representation(now)
            self.se = {}
            with libfaketime.fake_time(now):
                self.se[1] = SoundEffect.objects.create(name="sound_effect_1", sound_effect=file, created_by=self.user1)
                self.se[1].categories.add(self.category1)
                self.se[2] = SoundEffect.objects.create(name="sound_effect_2", sound_effect=file, created_by=self.user1)
                self.se[3] = SoundEffect.objects.create(name="sound_effect_3", sound_effect=file, created_by=self.user2)
                self.se[3].categories.add(self.category1)
                self.se[3].categories.add(self.category2)
        self._set_jwt_credentials(self.user1.username)

    def test_sound_effects(self):
        response = self.client.get(reverse("api:sound_effects"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), [
            {'id': 1,
             'created_at': self.created_at_drf,
             'created_by': "User1",
             'name': 'sound_effect_1',
             'my_total_play_count': 0,
             'my_30d_play_count': 0,
             'play_count_month': 0,
             'total_play_count': 0,
             'categories': ["category1"]},
            {'id': 2,
             'created_at': self.created_at_drf,
             'created_by': "User1",
             'name': 'sound_effect_2',
             'my_total_play_count': 0,
             'my_30d_play_count': 0,
             'play_count_month': 0,
             'total_play_count': 0,
             'categories': []
             },
            {'id': 3,
             'created_at': self.created_at_drf,
             'created_by': "User2",
             'name': 'sound_effect_3',
             'my_total_play_count': 0,
             'my_30d_play_count': 0,
             'play_count_month': 0,
             'total_play_count': 0,
             'categories': ["category1", "category2"]
             }])
        self.assertEqual(3, len(response.json()))

    def test_get_sound_effect(self):
        response = self.client.get(reverse("api:sound_effect", args=(self.se[1].id,)))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json(), {'id': self.se[1].id,
                                           'created_at': self.created_at_drf,
                                           'created_by': "User1",
                                           'name': 'sound_effect_1',
                                           'my_total_play_count': 0,
                                           'my_30d_play_count': 0,
                                           'play_count_month': 0,
                                           'total_play_count': 0,
                                           'categories': ["category1"]})

    def test_get_sound_effect_audio(self):
        response = self.client.get(reverse("api:sound_effect_audio", args=(self.se[1].id,)))
        self.assertEqual(response["content-type"], "audio/ogg")
        self.assertEqual(response.content, self.se[1].sound_effect.file.read(), "Returned wrong file?")

    def test_get_sound_effect_audio_higher_volume(self):
        response = self.client.get(reverse("api:sound_effect_audio", args=(self.se[1].id,)), {"volume": 1.5})
        self.assertEqual(response["content-type"], "audio/ogg")
        self.assertNotEqual(response.content, self.se[1].sound_effect.file.read(), "Returned wrong file?")
        # No idea how to test volume. Make sure the size is close to original
        self.assertTrue(self.se[1].sound_effect.size * 0.9 < len(response.content) < self.se[1].sound_effect.size * 1.1)

    def test_get_sound_effect_audio_lower_volume(self):
        response = self.client.get(reverse("api:sound_effect_audio", args=(1,)), {"volume": 0.5})
        self.assertEqual(response["content-type"], "audio/ogg")
        self.assertNotEqual(response.content, self.se[1].sound_effect.file.read(), "Returned wrong file?")
        # No idea how to test volume. Make sure the size is close to original
        self.assertTrue(self.se[1].sound_effect.size * 0.9 < len(response.content) < self.se[1].sound_effect.size * 1.1)
