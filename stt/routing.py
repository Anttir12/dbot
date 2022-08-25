from django.urls import path

from stt import consumers

websocket_urlpatterns = [
    path('ws/bot/stt/', consumers.SpeechConsumer.as_asgi(), name='stt'),
    path('ws/stt/feed/<str:stt_token>/', consumers.SpeechToTextOutputConsumer.as_asgi(), name="stt_feed_consumer"),
]
