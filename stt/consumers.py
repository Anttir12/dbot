import json
import logging
import threading
from typing import Optional
from urllib import parse

import channels.layers
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class SpeechConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        # Having this import at the top causes problems during deployment. Apparently it tries to access settings
        # before settings is ready
        from stt.SpeechAnalyzer import SttAnalyzer

        logger.info("initializing!")
        super(SpeechConsumer, self).__init__(*args, **kwargs)
        self.stt: Optional[SttAnalyzer] = None
        self.input_reader: Optional[threading.Thread] = None

    def connect(self):
        # Having this import at the top causes problems during deployment. Apparently it tries to access settings
        # before settings is ready
        from stt.SpeechAnalyzer import SttAnalyzer
        logger.info("Connection accepted!")
        channel_layer = channels.layers.get_channel_layer()
        token = parse.parse_qs(self.scope['query_string'].decode('utf-8')).get('wsToken', ['-'])[0]
        self.stt = SttAnalyzer(channel_layer, token)
        self.input_reader = threading.Thread(target=self.stt.input_reader)
        self.input_reader.start()
        self.accept()

    def disconnect(self, code):
        self.stt.end = True

    def receive(self, text_data: str = None, bytes_data: bytes = None):
        logger.info("Received data")
        if bytes_data:
            logger.info("bytes")
            self.stt.stream.put(bytes_data)


class SpeechToTextOutputConsumer(WebsocketConsumer):

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
