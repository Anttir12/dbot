from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import Sounds, play_sound

urlpatterns = [
    path('soundeffect/', staff_member_required(Sounds.as_view())),
    path('playsound/', play_sound, name="soundboard"),
]
