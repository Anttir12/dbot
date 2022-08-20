from django.urls import path

from stt import consumers

websocket_urlpatterns = [
    path('stt/', consumers.SpeechConsumer.as_asgi(), name='stt'),
]
