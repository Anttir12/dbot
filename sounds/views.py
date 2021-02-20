import logging

from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views import View
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from bot.bot import bot
from sounds import utils
from sounds.forms import SoundEffectUpload, SoundEffectFilter
from sounds import models


logger = logging.getLogger(__name__)


class Sounds(LoginRequiredMixin, View):

    def get(self, request):
        form = SoundEffectUpload()
        filter_form = SoundEffectFilter(request.user, request.GET)
        if filter_form.is_valid():
            query = Q()
            if filter_form.cleaned_data["categories"]:
                query = Q(categories__in=filter_form.cleaned_data["categories"])
            if filter_form.cleaned_data["categoryless"]:
                query = Q(query | Q(categories__isnull=True))
            sounds = models.SoundEffect.objects.filter(query)
            if filter_form.cleaned_data["favourite_list"]:
                sounds = sounds.filter(favourite_lists__in=filter_form.cleaned_data["favourite_list"])
        else:
            sounds = models.SoundEffect.objects.all()
        sounds = sounds.order_by("categories__name")
        return render(request, "sounds.html", {"form": form,
                                               "filter_form": filter_form,
                                               "sounds": sounds})

    @permission_required("sounds.can_upload_clip_from_yt", raise_exception=True)
    def post(self, request):
        form = SoundEffectUpload(request.POST, request.FILES)
        if form.is_valid():
            if "preview" in request.POST:
                preview_file = form.instance.sound_effect.file.file
                return HttpResponse(preview_file, content_type="audio/ogg")
            form.save()
            form = SoundEffectUpload()
        sounds = models.SoundEffect.objects.all()
        filter_form = SoundEffectFilter(request.user)
        return render(request, "sounds.html", {"form": form,
                                               "filter_form": filter_form,
                                               "sounds": sounds,
                                               })


@permission_required("sounds.can_download_sound", raise_exception=True)
def sound_audio(request, sound_id):
    vol = request.GET.get("volume")
    sound: models.SoundEffect = get_object_or_404(models.SoundEffect, id=sound_id)

    if vol:
        try:
            vol = float(vol)
            if 0.009 <= vol <= 5.001:
                file = utils.create_audio_file_modified_volume(sound.sound_effect.path, vol)
                response = HttpResponse(file, content_type="audio/ogg")
            else:
                raise ValueError()
        except ValueError:
            return HttpResponse(status=400)
    else:
        response = HttpResponse(sound.sound_effect.file, content_type="audio/ogg")
    return response


@permission_required("sounds.can_play_sound_with_bot", raise_exception=True)
def play_sound(request):
    user = request.user
    override = request.POST.get("override_sound", False)
    sound_id = request.POST.get("sound_id")
    sound_effect = get_object_or_404(models.SoundEffect, id=sound_id)
    played = async_to_sync(bot.skills.play_sound)(sound_effect, override=override)
    if played:
        models.SoundEffectPlayHistory.create_record(sound_effect=sound_effect, played_by=user)
    return HttpResponse(request, status=200)
