from django.urls import path

from stt.views import SttFeed

urlpatterns = [
    path('feed/<str:stt_token>', SttFeed.as_view(), name="stt_feed"),
]
