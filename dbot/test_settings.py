import tempfile

from dbot.settings import *  # noqa

TEST_DATA = os.path.join(BASE_DIR, "api", "tests", "test_data")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }
}

MEDIA_ROOT = tempfile.gettempdir()

CELERY_TASK_ALWAYS_EAGER = True
