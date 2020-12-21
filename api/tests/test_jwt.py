from django.contrib.auth.models import User
from django.urls import reverse

from api.tests.test import DbotApiTest


class JwtTest(DbotApiTest):

    def setUp(self):
        self.user1 = User.objects.create_user("User1", "test1@example.com", "x")

    def test_jwt_login(self):
        response = self.client.post(reverse("api:token_obtain_pair"), data={"username": self.user1.username,
                                                                            "password": "x"})
        self.assertContains(response, "refresh")
        self.assertContains(response, "access")

    def test_jwt_refresh(self):
        refresh_token = self._set_jwt_credentials(self.user1.username)[1]
        response = self.client.post(reverse("api:token_refresh"), data={"refresh": refresh_token})
        self.assertContains(response, "access")
