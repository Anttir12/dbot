import os

import libfaketime
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers, status

from api.tests.test import DbotApiTest
from sounds.models import SoundEffect, Favourites, SoundEffectPlayHistory


class FavouritesTest(DbotApiTest):

    def setUp(self):
        bot_users = Group.objects.get(name="Bot user")
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")
        self.user2 = User.objects.create_user("User2", "test2@example.com", "x")
        bot_users.user_set.add(self.user1)
        bot_users.user_set.add(self.user2)
        Favourites.objects.create(name="user2 favourites", owner=self.user2)
        path = os.path.join(settings.TEST_DATA, "nerd.ogg")
        with open(path, "rb") as audio:
            size = os.path.getsize(path)
            file = InMemoryUploadedFile(audio, "sound_effect", audio.name, None, size, None)
            now = timezone.now()
            self.created_at_drf = serializers.DateTimeField().to_representation(now)
            with libfaketime.fake_time(now):
                self.se1 = SoundEffect.objects.create(name="sound_effect_1", sound_effect=file, created_by=self.user1)
                self.se2 = SoundEffect.objects.create(name="sound_effect_2", sound_effect=file, created_by=self.user1)
                self.se3 = SoundEffect.objects.create(name="sound_effect_3", sound_effect=file, created_by=self.user1)

    def test_get_all_favourites(self):
        favs1 = Favourites.objects.create(name="favs1", owner=self.user1)
        favs1.sound_effects.add(self.se1)
        favs2 = Favourites.objects.create(name="favs2", owner=self.user1)
        favs2.sound_effects.add(self.se2)
        favs3 = Favourites.objects.create(name="favs3", owner=self.user1)
        favs3.sound_effects.add(self.se1)
        favs3.sound_effects.add(self.se2)
        favs3.sound_effects.add(self.se3)
        self._set_jwt_credentials(self.user1.username)
        response = self.client.get(reverse("api:favourites"), format="json")
        self.assertEqual(response.json(), [{'id': favs1.id,
                                            'name': 'favs1',
                                            'sound_effects': [{'id': 1,
                                                               'name': 'sound_effect_1'}]},
                                           {'id': favs2.id,
                                            'name': 'favs2',
                                            'sound_effects': [{'id': 2,
                                                               'name': 'sound_effect_2'}]},
                                           {'id': favs3.id,
                                            'name': 'favs3',
                                            'sound_effects': [{'id': 1,
                                                               'name': 'sound_effect_1'},
                                                              {'id': 2,
                                                               'name': 'sound_effect_2'},
                                                              {'id': 3,
                                                               'name': 'sound_effect_3'}]}
                                           ])

    def test_get_favourite(self):
        favs = Favourites.objects.create(name="favs", owner=self.user1)
        favs.sound_effects.add(self.se1)
        favs.sound_effects.add(self.se2)
        favs.sound_effects.add(self.se3)
        self._set_jwt_credentials(self.user1.username)
        response = self.client.get(reverse("api:favourites_detail", args=(favs.id,)), format="json")
        self.assertEqual(response.json(), {'id': favs.id,
                                           'name': 'favs',
                                           'sound_effects': [{'id': 1,
                                                              'name': 'sound_effect_1'},
                                                             {'id': 2,
                                                              'name': 'sound_effect_2'},
                                                             {'id': 3,
                                                              'name': 'sound_effect_3'}]}
                         )

    def test_get_no_favourites(self):
        self._set_jwt_credentials(self.user1.username)
        response = self.client.get(reverse("api:favourites"), format="json")
        self.assertEqual(response.json(), [])

    def test_create_empty_favourite(self):
        self._set_jwt_credentials(self.user1.username)
        response = self.client.post(reverse("api:favourites"), {"name": "myfavourites"}, format="json")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.content)
        my_favourites: Favourites = Favourites.objects.get(name="myfavourites")
        self.assertFalse(my_favourites.sound_effects.all())

    def test_add_sounds_to_favourite(self):
        self._set_jwt_credentials(self.user1.username)
        favs = Favourites.objects.create(name="myfavourites", owner=self.user1)
        response = self.client.post(reverse("api:favourites_sound_effects", args=(favs.id,)), format="json",
                                    data={"sound_effects": [self.se2.id, self.se3.id]})
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
        my_favourites: Favourites = Favourites.objects.get(name="myfavourites")
        self.assertTrue(my_favourites.sound_effects.filter(name="sound_effect_2").exists())
        self.assertTrue(my_favourites.sound_effects.filter(name="sound_effect_3").exists())

    def test_add_sound_to_missing_favourites(self):
        self._set_jwt_credentials(self.user1.username)
        response = self.client.post(reverse("api:favourites_sound_effects", args=(32,)), format="json",
                                    data={"sound_effects": [self.se2.id, self.se3.id]})
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_add_sound_to_other_user_favourites(self):
        self._set_jwt_credentials(self.user1.username)
        favs = Favourites.objects.create(name="myfavourites", owner=self.user2)
        response = self.client.post(reverse("api:favourites_sound_effects", args=(favs.id,)), format="json",
                                    data={"sound_effects": [self.se2.id, self.se3.id]})
        favs.refresh_from_db()
        self.assertFalse(favs.sound_effects.filter(name="sound_effect_2").exists())
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code, response.content)

    def test_remove_sound_from_favourites(self):
        self._set_jwt_credentials(self.user1.username)
        favs = Favourites.objects.create(name="myfavourites", owner=self.user1)
        favs.sound_effects.add(self.se1)
        favs.sound_effects.add(self.se2)
        favs.sound_effects.add(self.se3)
        self.assertEqual(favs.sound_effects.count(), 3)
        response = self.client.delete(reverse("api:favourites_sound_effects", args=(favs.id,)), format="json",
                                      data={"sound_effects": [self.se1.id, self.se3.id]})
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, favs.sound_effects.count())
        self.assertTrue(favs.sound_effects.filter(id=self.se2.id).exists())

    def test_get_favourite_sound_effects(self):
        self._set_jwt_credentials(self.user1.username)
        favs = Favourites.objects.create(name="myfavourites", owner=self.user1)
        SoundEffectPlayHistory.create_record(self.se1, self.user1)
        favs.sound_effects.add(self.se1)
        favs.sound_effects.add(self.se2)
        favs.sound_effects.add(self.se3)
        self.assertEqual(favs.sound_effects.count(), 3)
        response = self.client.get(reverse("api:favourites_sound_effects", args=(favs.id,)), format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.json(), [{'id': 1,
                                            'created_at': self.created_at_drf,
                                            'created_by': 'User1',
                                            'name': 'sound_effect_1',
                                            'my_total_play_count': 1,
                                            'my_play_count_month': 1,
                                            'play_count_month': 1,
                                            'total_play_count': 1,
                                            'categories': []},
                                           {'id': 2,
                                            'created_at': self.created_at_drf,
                                            'created_by': 'User1',
                                            'name': 'sound_effect_2',
                                            'my_total_play_count': 0,
                                            'my_play_count_month': 0,
                                            'play_count_month': 0,
                                            'total_play_count': 0,
                                            'categories': []},
                                           {'id': 3,
                                            'created_at': self.created_at_drf,
                                            'created_by': 'User1',
                                            'name': 'sound_effect_3',
                                            'my_total_play_count': 0,
                                            'my_play_count_month': 0,
                                            'play_count_month': 0,
                                            'total_play_count': 0,
                                            'categories': []}])
