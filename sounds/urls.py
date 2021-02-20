from django.urls import path
from django.views.generic import RedirectView

from .views import Sounds, play_sound, sound_audio

urlpatterns = [
    path('dashboard/', Sounds.as_view(), name="dashboard"),
    path('soundeffect/', RedirectView.as_view(url='/')),
    path('sound_effect/<int:sound_id>', sound_audio, name="sound_audio"),
    path('playsound/', play_sound, name="play_sound"),
]
