from django.urls import path

from stt import consumers

websocket_urlpatterns = [
    path('ws/bot/stt/', consumers.GptVoiceConsumer.as_asgi(), name='stt'),
    path('ws/bot/gpt/', consumers.GptTextConsumer.as_asgi(), name='gpt'),
    path('ws/stt/feed/<str:stt_token>/', consumers.SpeechToTextOutputConsumer.as_asgi(), name="stt_feed_consumer"),
]
