import logging

from django.db.models import Q
from django.views import View
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from sounds import tasks, utils
from sounds.forms import SoundEffectUpload, SoundEffectFilter
from sounds.models import SoundEffect


logger = logging.getLogger(__name__)


class Sounds(View):

    def get(self, request):
        form = SoundEffectUpload()
        filter_form = SoundEffectFilter(request.user, request.GET)
        if filter_form.is_valid():
            query = Q()
            if filter_form.cleaned_data["categories"]:
                query = Q(categories__in=filter_form.cleaned_data["categories"])
            if filter_form.cleaned_data["categoryless"]:
                query = Q(query | Q(categories__isnull=True))
            sounds = SoundEffect.objects.filter(query)
            if filter_form.cleaned_data["favourite_list"]:
                sounds = sounds.filter(favourite_lists__in=filter_form.cleaned_data["favourite_list"])
        else:
            sounds = SoundEffect.objects.all()
        sounds = sounds.order_by("categories__name")
        return render(request, "sounds.html", {"form": form,
                                               "filter_form": filter_form,
                                               "sounds": sounds})

    def post(self, request):
        form = SoundEffectUpload(request.POST, request.FILES)
        if form.is_valid():
            if "preview" in request.POST:
                preview_file = form.instance.sound_effect.file.file
                return HttpResponse(preview_file, content_type="audio/ogg")
            form.save()
            form = SoundEffectUpload()
        sounds = SoundEffect.objects.all()
        filter_form = SoundEffectFilter(request.user)
        return render(request, "sounds.html", {"form": form,
                                               "filter_form": filter_form,
                                               "sounds": sounds,
                                               })


@staff_member_required
def sound_audio(request, sound_id):
    vol = request.GET.get("volume")
    sound: SoundEffect = get_object_or_404(SoundEffect, id=sound_id)

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


@staff_member_required
def play_sound(request):
    override = request.POST.get("override_sound", False)
    sound_id = request.POST.get("sound_id")
    if not SoundEffect.objects.filter(id=sound_id).exists():
        return HttpResponse(request, status=404)
    tasks.play_sound.delay(sound_id, override)
    return HttpResponse(request, status=200)
