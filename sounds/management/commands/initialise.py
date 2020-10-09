import logging
import os

from django.contrib.auth.models import User
from django.core.management import BaseCommand

logger = logging.getLogger("Initialise")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        email = os.environ.get("SUPER_EMAIL")
        password = os.environ.get("SUPER_PASSWORD")
        if email and password:
            if User.objects.count() == 0:

                User.objects.create_superuser("admin", email, password)
                logger.info("Superuser created")
            else:
                logger.info("A user already exists")
        else:
            logger.info("Skipping super user creation. Missing SUPER_EMAIL and/or SUPER_PASSWORD")
