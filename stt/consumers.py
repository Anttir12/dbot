import logging
import threading
from typing import Optional

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
        self.stt = SttAnalyzer()
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
