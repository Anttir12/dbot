import json
import logging
import threading
from typing import Optional
from urllib import parse

import channels.layers
import openai
import redis
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from constance import config

from dbot import settings

logger = logging.getLogger(__name__)


class SpeechConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        # Having this import at the top causes problems during deployment. Apparently it tries to access settings
        # before settings is ready
        from stt.speech_analyzer import SttAnalyzer

        logger.info("initializing!")
        super().__init__(*args, **kwargs)
        self.stt: Optional[SttAnalyzer] = None
        self.input_reader: Optional[threading.Thread] = None

    def _send_voice(self, bytes_data: bytes):
        self.send(bytes_data=bytes_data)

    def connect(self):
        # Having this import at the top causes problems during deployment. Apparently it tries to access settings
        # before settings is ready
        from stt.speech_analyzer import SttAnalyzer
        logger.info("Connection accepted!")
        channel_layer = channels.layers.get_channel_layer()
        token = parse.parse_qs(self.scope['query_string'].decode('utf-8')).get('wsToken', ['-'])[0]
        self.stt = SttAnalyzer(channel_layer, token, self._send_voice)
        self.input_reader = threading.Thread(target=self.stt.input_reader)
        self.input_reader.start()
        self.accept()

    def disconnect(self, code):
        self.stt.end = True

    def receive(self, text_data: str = None, bytes_data: bytes = None):
        if bytes_data:
            self.stt.stream.put(bytes_data)


class SpeechToTextOutputConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self.stt_token = None
        super().__init__(*args, **kwargs)

    def connect(self):
        self.stt_token = self.scope['url_route']['kwargs']['stt_token']

        async_to_sync(self.channel_layer.group_add)(
            self.stt_token,
            self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.stt_token,
            self.channel_name
        )

    def recognizing(self, event):
        text = event['text']

        self.send(text_data=json.dumps({
            'type': 'recognizing',
            'text': text
        }))

    def recognized(self, event):
        text = event['text']

        self.send(text_data=json.dumps({
            'type': 'recognized',
            'text': text
        }))

    def chatgpt(self, event):
        text = event['text']

        self.send(text_data=json.dumps({
            'type': 'chatgpt',
            'text': text
        }))


class GptConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self.r = redis.StrictRedis.from_url(settings.BOT_REDIS_URL, decode_responses=True)
        self.gpt_messages = "chatbot:gptmessages"
        super().__init__(*args, **kwargs)

    def connect(self):
        logger.info("GPT-4 Connection accepted!")
        self.accept()

    def send_json(self, json_message: dict):
        self.send(json.dumps(json_message))

    def receive(self, text_data: str = None, bytes_data: bytes = None):

        if text_data:
            logger.info("Sending this to GTP-4: {}".format(text_data))
            self.r.rpush(self.gpt_messages, f"user|{text_data}")
            gpt_messages = self.r.lrange(self.gpt_messages, 0, -1)
            messages = [{"role": "system", "content": config.CHATGPT_SYSTEM_MESSAGE}]

            for gptm in gpt_messages:
                role, content = gptm.split("|", 1)
                messages.append({"role": role, "content": content})

            openai.api_key = settings.OPENAPI_KEY
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                stream=True
            )
            entire_response = ""
            for chunk in response:
                if content := chunk["choices"][0]["delta"].get("content"):
                    entire_response += content
                    self.send_json({"type": "chunk", "content": content})

            self.send_json({"type": "end"})
            self.r.rpush(self.gpt_messages, f"assistant|{entire_response}")
            self.r.ltrim(self.gpt_messages, 0, 9)
            self.r.expire(self.gpt_messages, 300)
            messages.append(f"assistant|{entire_response}")
            logger.info("GTP-4 responded with: {}".format(entire_response))
