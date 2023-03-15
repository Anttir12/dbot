import logging
import pprint
from typing import Callable, Optional

import openai
import redis
from asgiref.sync import async_to_sync
from constance import config
from django.conf import settings
from django.utils.encoding import force_str

from stt.speech_synthesis import SpeechSynthesis

r = redis.StrictRedis.from_url(settings.BOT_REDIS_URL, decode_responses=True)
CHATBOT_MESSAGES = "chatbot:messages"

logger = logging.getLogger(__name__)


class ChatBot:

    def __init__(self, send_speech_bytes: Callable, channel_layer, token):
        self.keywords = config.CHATGPT_TRIGGER_PHRASE.split(";")
        self.speech_synthesis = SpeechSynthesis()
        self.send_speech_bytes = send_speech_bytes
        self.channel_layer = channel_layer
        self.token = token
        self._conversation_mode = False
        self._start_conversation_mode_phrase = config.CHATGPT_START_CONVERSATION.split(";")
        self._stop_conversation_mode_phrase = config.CHATGPT_STOP_CONVERSATION.split(";")
        self._ack_response: Optional[bytes] = None
        if ack_text := getattr(config, "CHATGPT_TRIGGER_PHRASE_ACKNOWLEDGEMENT", None):
            self._ack_response = self.speech_synthesis.text_to_speech(ack_text)
        self._enable_conversation_voice: Optional[bytes] = None
        self._disable_conversation_voice: Optional[bytes] = None

    @property
    def conversation_mode(self) -> bool:
        return self._conversation_mode

    @conversation_mode.setter
    def conversation_mode(self, mode: bool):
        logger.info("set conversation mode {}".format(mode))
        old_mode = self._conversation_mode
        self._conversation_mode = mode
        if old_mode and not mode:
            if not self._disable_conversation_voice:
                self._disable_conversation_voice = \
                    self.speech_synthesis.text_to_speech(config.CHATGPT_CONVERSATION_MODE_DISABLED)
            self.send_speech_bytes(self._disable_conversation_voice)
        else:
            if not self._enable_conversation_voice:
                self._enable_conversation_voice = \
                    self.speech_synthesis.text_to_speech(config.CHATGPT_CONVERSATION_MODE_ENABLED)
            self.send_speech_bytes(self._enable_conversation_voice)

    def chat(self, text: str):
        lowered_dotless_text = text.lower().replace(".", "").replace(",", "")
        if not lowered_dotless_text:
            return False

        if self.conversation_mode and lowered_dotless_text in self._stop_conversation_mode_phrase:
            self.conversation_mode = False

        send_to_chat_gpt = self.conversation_mode
        if not send_to_chat_gpt:
            for keyword in self.keywords:
                i = lowered_dotless_text.find(keyword)
                if i >= 0:
                    text = text[i + len(keyword):]
                    send_to_chat_gpt = True
                    break

        if not self.conversation_mode and lowered_dotless_text in self._start_conversation_mode_phrase:
            self.conversation_mode = True

        if send_to_chat_gpt:
            r.rpush(CHATBOT_MESSAGES, f"user|{text}")
            logger.info("Sending this to ChatGTP: {}".format(text))
            chatbot_messages = r.lrange(CHATBOT_MESSAGES, 0, -1)
            messages = [{"role": "system", "content": config.CHATGPT_SYSTEM_MESSAGE}]
            for cbm in chatbot_messages:
                role, content = cbm.split("|", 1)
                messages.append({"role": role, "content": content})
            try:
                if self._ack_response:
                    self.send_speech_bytes(self._ack_response)
                openai.api_key = settings.OPENAPI_KEY
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                )
                response_text: str = force_str(response["choices"][0]["message"]["content"])
                messages.append({"role": "assistant", "content": response_text})
                pprint.pprint(messages)
                r.rpush(CHATBOT_MESSAGES, f"assistant|{response_text}")
                r.expire(CHATBOT_MESSAGES, 300)
                logger.info("ChatGTP responded with: {}".format(response_text))
                if self.channel_layer and self.token:
                    async_to_sync(self.channel_layer.group_send)(self.token, {
                        'type': 'chatgpt', 'text': response_text})
                speech_bytes = self.speech_synthesis.text_to_speech(response_text)
                self.send_speech_bytes(speech_bytes)
                return True
            except Exception as e:
                logger.error("Something went wrong")
                logger.exception(e)
        return False
