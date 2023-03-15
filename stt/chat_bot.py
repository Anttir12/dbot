import logging
import math
from typing import Callable, Optional

import openai
import redis
from asgiref.sync import async_to_sync
from constance import config
from django.conf import settings

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
        with open("acksound.opus", "rb") as ackfile:
            self._ack_response: Optional[bytes] = ackfile.read()
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
                    stream=True
                )
                entire_response = ""
                chunk_for_voice = ""
                minimum_word_count = 1
                for chunk in response:
                    if content := chunk["choices"][0]["delta"].get("content"):
                        chunk_for_voice += content
                        chunk_word_count = len(chunk_for_voice.split(" "))
                        char_offset = len(" ".join(chunk_for_voice.split(" ", minimum_word_count)[:minimum_word_count]))
                        entire_response += content
                        if chunk_word_count > minimum_word_count:
                            for i, c in enumerate(chunk_for_voice[char_offset:]):
                                i += char_offset
                                if c in ".,!?;:":
                                    to_send = chunk_for_voice[:i+1]
                                    minimum_word_count = min(64, math.ceil(len(to_send.split(" ")) * 1.5))
                                    chunk_for_voice = chunk_for_voice[i+1:]
                                    speech_bytes = self.speech_synthesis.text_to_speech(to_send)
                                    self.send_speech_bytes(speech_bytes)
                                    break
                if len(chunk_for_voice) > 1:
                    speech_bytes = self.speech_synthesis.text_to_speech(chunk_for_voice)
                    self.send_speech_bytes(speech_bytes)
                messages.append({"role": "assistant", "content": entire_response})
                r.rpush(CHATBOT_MESSAGES, f"assistant|{entire_response}")
                r.expire(CHATBOT_MESSAGES, 300)
                logger.info("ChatGTP responded with: {}".format(entire_response))
                if self.channel_layer and self.token:
                    async_to_sync(self.channel_layer.group_send)(self.token, {
                        'type': 'chatgpt', 'text': entire_response})
                return True
            except Exception as e:
                logger.error("Something went wrong")
                logger.exception(e)
        return False
