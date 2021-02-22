import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views import View
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

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

    def post(self, request):
        if not request.user.has_perm("sounds.can_upload_clip_from_yt"):
            return HttpResponseForbidden()
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
