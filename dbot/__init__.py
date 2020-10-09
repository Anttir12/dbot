"""
Ensures app celery_app is loaded when django starts
"""
from .celery import app as celery_app
__all__ = ('celery_app',)
