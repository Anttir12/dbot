import os

from django.urls import reverse
from rest_framework.test import APITestCase

from sounds.models import SoundEffect


class DbotApiTest(APITestCase):

    def tearDown(self):
        for s in SoundEffect.objects.all():
            try:
                os.remove(s.sound_effect.path)
            except OSError:
                pass

    def _set_jwt_credentials(self, username, password="x"):
        response = self.client.post(reverse("api:token_obtain_pair"), data={"username": username,
                                                                            "password": password})
        # No idea why pylint complains about this (it clearly works). Disabling the no-member for next line
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')  # pylint: disable=no-member
        return response.data["access"], response.data["refresh"]
