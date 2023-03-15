import queue
import random
import string
import subprocess
import logging
import threading
import time
from queue import Queue
from typing import Optional, Collection, List, Set, Callable

import azure.cognitiveservices.speech as speechsdk
from asgiref.sync import async_to_sync
from azure.cognitiveservices.speech import ProfanityOption, SpeechRecognitionEventArgs, OutputFormat, \
    SpeechRecognitionCanceledEventArgs
from azure.cognitiveservices.speech.audio import PushAudioInputStream
from django.conf import settings

from bot import dbot_skills
from sounds import models as sound_models
from stt import models
from stt.chat_bot import ChatBot

logger = logging.getLogger(__name__)


BLANK_FRAME = b'1O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00OggS\x00\x00\x00\x15\t\x00\x00\x00\x00\x00\x01\x00\x00\x00?\x00\x00\x00\tH\x19\xcd\nKKKKKKKKKKx\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00OggS\x00\x00\x80:\t\x00\x00\x00\x00\x00\x01\x00\x00\x00@\x00\x00\x00\xf8\x08\x1dG\nKKKKKKKKKKx\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00OggS\x00\x00\x00`\t\x00\x00\x00\x00\x00\x01\x00\x00\x00A\x00\x00\x00N\xe6u3\nKKKKKKKKKKx\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00OggS\x00\x00\x80\x85\t\x00\x00\x00\x00\x00\x01\x00\x00\x00B\x00\x00\x00I\xa8\xbd\n\nKKKKKKKKKKx\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00OggS\x00\x00\x00\xab\t\x00\x00\x00\x00\x00\x01\x00\x00\x00C\x00\x00\x00D\xec\x9dP\nKKKKKKKKKKx\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e\x91y\xbe\xd0LP\x1f\n\xd8\xd71O\xcc\xceb!\x9di\xe9\xb48\x12<znu\xb48\x12<\x00x\x07\xc9y\xc8\xc9W\xc0\xa2\x12#\xfa\xefg\xf3\x12c\xa9\xe0\x81\x96Q\x7f\x15\xb0v+p\x9a\xbf\x94\xd4\x08\x1aXh\x03\x92\xff\xf5\\\x04\xf8\x8e'
CHUNK_SIZE = 4000


class AnyPhrase:

    def __init__(self, reaction_model: models.SttReaction):
        if not (any_phrases := reaction_model.data.get("any_phrase")):
            raise ValueError("Invalid type")
        logger.info("Looking for phareses:")
        self.any_phrases = set(any_phrases)
        logger.info(self.any_phrases)
        self.cooldown = reaction_model.cooldown
        self.sounds: List[sound_models.SoundEffect] = list(reaction_model.sound_effects.all())
        self.last_match = 0

    def match(self, tokenized_text: Set[str]) -> bool:
        matched = False
        if (time.time() - self.last_match) > self.cooldown:
            matched = any(True for token in tokenized_text if token in self.any_phrases)
            if matched:
                self.last_match = time.time()

        return matched


class SttAnalyzer:

    def __init__(self, channel_layer=None, token: str = None, send: Callable = None):
        self.input_data: Optional[bytes] = None
        self.last_read = None
        self.empty_frames = 0
        self.end = False
        self.stream = Queue()
        reaction_models = list(models.SttReaction.objects.filter(active=True))
        self.reactions: Collection[AnyPhrase] = self._unpack_reaction_models(reaction_models)
        self.channel_layer = channel_layer
        self.token = token
        self.chat_bot = ChatBot(send_speech_bytes=send, channel_layer=channel_layer, token=token)
        if self.channel_layer and not self.token:
            raise ValueError("Token required with channel layer")

    def _unpack_reaction_models(self, reaction_models: Collection[models.SttReaction]):
        reactions = []
        for reaction in reaction_models:
            reactions.append(AnyPhrase(reaction))
        return reactions

    def input_reader(self):
        logger.info("Input reader started!")

        command = [
            settings.FFMPEG_PATH,
            '-loglevel', 'quiet',
            '-f', 'ogg',
            '-i', 'pipe:',
            '-ar', '16000',
            '-ac', '1',
            '-f', 's16le',
            'pipe:'
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        t = threading.Thread(target=self.azure, args=(process,))
        t.start()

        while True:
            frame = None
            if self.end:
                logger.info("ENDING THIS")
                process.kill()
                break

            now = time.time()
            try:
                frame = self.stream.get(block=False)
                self.last_read = time.time()
                self.empty_frames = 0
            except queue.Empty:
                if self.empty_frames < 5 and (
                        (self.last_read and now - self.last_read > 0.75) or
                        (self.last_read and self.empty_frames > 0 and now - self.last_read > 0.125)):
                    self.empty_frames += 1
                    self.last_read = time.time()
                    frame = BLANK_FRAME

            if frame:
                process.stdin.write(frame)
                process.stdin.flush()
            else:
                time.sleep(0.1)

        t.join()

    def push_stream_writer(self, process: subprocess.Popen, stream: PushAudioInputStream):
        try:
            while True:
                output_data = process.stdout.read(CHUNK_SIZE)
                if len(output_data) > 0:
                    stream.write(output_data)
                elif self.end:
                    break
        except Exception as exception:
            logger.info("Error in push_stream_writer")
            raise exception
        finally:
            stream.close()  # must be done to signal the end of stream

    @staticmethod
    def split_into_phrases(text: str, max_size: Optional[int] = None):
        text.translate(str.maketrans('', '', string.punctuation)).lower()
        words = text.split()
        final_phrases = []
        word_count = len(words)
        for i in range(0, word_count):
            temp_phrases: List[str] = []
            max_words = min(word_count, i + max_size) if max_size else word_count
            for j in range(i, max_words):
                if temp_phrases:
                    phrases = temp_phrases[-1]
                else:
                    phrases = ""
                if phrases:
                    phrases += " "
                phrases += f"{words[j]}"
                temp_phrases.append(phrases)
            final_phrases.extend(temp_phrases)
        return set(final_phrases)

    def azure(self, process: subprocess.Popen):
        """gives an example how to use a push audio stream to recognize speech from a custom audio
        source"""
        speech_config = speechsdk.SpeechConfig(subscription=settings.AZURE_KEY, region="northeurope")
        speech_config.speech_recognition_language = "fi-FI"
        speech_config.set_profanity(ProfanityOption.Raw)
        speech_config.output_format = OutputFormat.Detailed

        # setup the audio stream
        stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=stream)

        # instantiate the speech recognizer with push stream input
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        recognition_done = threading.Event()

        # Connect callbacks to the events fired by the speech recognizer
        def session_stopped_cb(evt):
            """callback that signals to stop continuous recognition upon receiving an event `evt`"""
            logger.info('SESSION STOPPED: {}'.format(evt))
            recognition_done.set()

        def recognizing(evt: SpeechRecognitionEventArgs):
            analyse(evt)
            print(f"Recognizing: {evt.result.text}")
            if self.channel_layer:
                async_to_sync(self.channel_layer.group_send)(self.token, {'type': 'recognizing',
                                                                          'text': evt.result.text})

        def recognized(evt: SpeechRecognitionEventArgs):
            analyse(evt)
            text = evt.result.text
            print(f"recognized: {text}")
            if self.channel_layer:
                async_to_sync(self.channel_layer.group_send)(self.token, {'type': 'recognized',
                                                                          'text': text})
            if text.strip():
                # This is a blocking call. It is intentional. This way the bot won't process something until the
                # previous is done processing. Does not seem to cause any problems
                self.chat_bot.chat(text)

        def analyse(evt: SpeechRecognitionEventArgs):
            tokenized_text = self.split_into_phrases(evt.result.text)
            for reaction in self.reactions:
                if reaction.match(tokenized_text):
                    sound = random.choice(reaction.sounds)
                    async_to_sync(dbot_skills.play_sound)(sound)

        speech_recognizer.recognizing.connect(recognizing)
        speech_recognizer.recognized.connect(recognized)
        speech_recognizer.session_started.connect(lambda evt: logger.info('SESSION STARTED: {}'.format(evt)))
        speech_recognizer.session_stopped.connect(session_stopped_cb)

        def cancelled(evt: SpeechRecognitionCanceledEventArgs):
            logger.info('CANCELED {}'.format(evt))
            print(evt.__dict__)
            print(evt.cancellation_details)

        speech_recognizer.canceled.connect(cancelled)

        # start push stream writer thread
        push_stream_writer_thread = threading.Thread(target=self.push_stream_writer, args=[process, stream])
        push_stream_writer_thread.start()

        # start continuous speech recognition
        speech_recognizer.start_continuous_recognition()

        # wait until all input processed
        recognition_done.wait()

        # stop recognition and clean up
        speech_recognizer.stop_continuous_recognition()
        push_stream_writer_thread.join()