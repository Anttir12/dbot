import logging

from django.views import View
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from . import tasks
from .forms import SoundEffectUpload
from .models import SoundEffect


logger = logging.getLogger(__name__)


class Sounds(View):
    def get(self, request):
        form = SoundEffectUpload()
        sounds = SoundEffect.objects.all()
        return render(request, "sounds.html", {"form": form, "sounds": sounds})

    def post(self, request):
        form = SoundEffectUpload(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            form = SoundEffectUpload()
        sounds = SoundEffect.objects.all()
        return render(request, "sounds.html", {"form": form, "sounds": sounds})


@staff_member_required
def play_sound(request):
    override = request.POST.get("override_sound", False)
    sound_id = request.POST.get("sound_id")
    if not SoundEffect.objects.filter(id=sound_id).exists():
        return HttpResponse(request, status=404)
    tasks.play_sound.delay(sound_id, override)
    return HttpResponse(request, status=200)
