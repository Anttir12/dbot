from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from sounds.models import SoundEffect


class ApiTest(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")
        self.user2 = User.objects.create_user("User2", "test2@example.com", "x")
        for i in range(10):
            SoundEffect.objects.create(name=f"sound_effect_{i}", sound_effect="foo.bar")

    def test_jwt_login(self):
        response = self.client.post(reverse("token_obtain_pair"), data={"username": self.user1.username,
                                                                        "password": "x"})
        self.assertContains(response, "refresh")
        self.assertContains(response, "access")

    def test_sound_effects(self):
        self._set_jwt_credentials(self.user1.username)
        response = self.client.get(reverse("api_sound_effects"))
        self.assertEqual(10, len(response.json()))

    def _set_jwt_credentials(self, username, password="x"):
        response = self.client.post(reverse("token_obtain_pair"), data={"username": username,
                                                                        "password": password})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
