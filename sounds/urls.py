from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.views.generic import RedirectView

from .views import Sounds, play_sound, sound_audio

urlpatterns = [
    path('', staff_member_required(Sounds.as_view()),),
    path('soundeffect/', RedirectView.as_view(url='/')),
    path('sound_effect/<int:sound_id>', sound_audio, name="sound_audio"),
    path('playsound/', play_sound, name="play_sound"),
]
