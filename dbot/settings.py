"""
Django settings for dbot project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import datetime
import os
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from django.core.validators import MaxValueValidator, MinValueValidator

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    SECRET_KEY=(str, '#ar#b0j$id-m17@y7a4koc2ihtzdykexj+0_=7-ys!g9-txm3='),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DATABASE_ENGINE=(str, 'django.db.backends.postgresql'),
    DATABASE_NAME=(str, "dbot-db"),
    DATABASE_USER=(str, 'dbot_user'),
    DATABASE_PASSWORD=(str, 'OMWDESYBPASSWORD'),
    DATABASE_HOST=(str, '127.0.0.1'),
    DATABASE_PORT=(int, 5432),
    CONSTANCE_REDIS_URL=(str, 'redis://localhost:6379/8'),
    BOT_REDIS_URL=(str, 'redis://localhost:6379/7'),
    STATIC_ROOT=(str, os.path.join(BASE_DIR, 'static/')),
    COMMAND_PREFIX=(str, "!"),
    DISCORD_TOKEN=(str, ""),
    DISCORD_GUILD=(str, ""),
    MAX_CACHED_STREAMS=(int, 3),
    FFMPEG_PATH=(str, "ffmpeg"),
    FFPROBE_PATH=(str, "ffprobe"),
    AZURE_KEY=(str, "")
)
environ.Env.read_env()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sounds.apps.SoundsConfig',
    'bot.apps.BotConfig',
    'stt.apps.SttConfig',
    'crispy_forms',
    'django_extensions',
    'django_cleanup.apps.CleanupConfig',
    'colorfield',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'constance',
    'channels'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dbot.wsgi.application'
ASGI_APPLICATION = 'dbot.asgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env("DATABASE_ENGINE"),
        'NAME':  env("DATABASE_NAME"),
        'USER': env("DATABASE_USER"),
        'PASSWORD': env("DATABASE_PASSWORD"),
        'HOST': env("DATABASE_HOST"),
        'PORT': env("DATABASE_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

LOGIN_REDIRECT_URL = "dashboard"
LOGIN_URL = "login"

STATIC_URL = '/static/'

STATIC_ROOT = env("STATIC_ROOT")

APPEND_SLASH = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

COMMAND_PREFIX = env("COMMAND_PREFIX")

RUN_BOT = True

DISCORD_TOKEN = env("DISCORD_TOKEN")
DISCORD_GUILD = env("DISCORD_GUILD")

MAX_CACHED_STREAMS = env("MAX_CACHED_STREAMS")

FFMPEG_PATH = env("FFMPEG_PATH")
FFPROBE_PATH = env("FFPROBE_PATH")

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

CORS_ALLOWED_ORIGINS = [
    "https://localhost:3000",
    "https://beta.dbot.devduck.fi",
    "https://www.beta.dbot.devduck.fi",
]

if DEBUG:
    # In debug mode keep the access token alive for a long time
    SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60)}

# SSL/HTTPS
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# CONSTANCE

CONSTANCE_REDIS_CONNECTION = env('CONSTANCE_REDIS_URL')

CONSTANCE_ADDITIONAL_FIELDS = {
    'min_1_max_10': ['django.forms.fields.IntegerField', {
        'validators': [MaxValueValidator(10), MinValueValidator(1)]
    }]
}
CONSTANCE_CONFIG = {
    "MAX_QUEUE_SIZE": (3, "Max queue size for sound effects", "min_1_max_10"),
    "SOUNDS_ONLY_FROM_CHANNEL": (False, "Sound effects can only be triggered by users from the "
                                        "same channel as bot (NYI)"),
}

AZURE_KEY = env("AZURE_KEY")

BOT_REDIS_URL = env("BOT_REDIS_URL")
