"""
Setup celery
"""

import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbot.settings')

app = Celery('dbot')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
