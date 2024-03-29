import os
import sys

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from . import utils
from .models import SoundEffect, Category, Favourites
from .utils import YtException


class SoundEffectUpload(forms.ModelForm):

    yt_url = forms.CharField(label="YouTube URL", max_length=200, required=True)
    start_ms = forms.IntegerField(label="Start time (ms)", required=False)
    end_ms = forms.IntegerField(label="End time (ms)", required=False)
    tenor_url = forms.CharField(label="Tenor url", required=False)

    class Meta:
        model = SoundEffect
        fields = ("name", "yt_url", "categories", "start_ms", "end_ms")
        widgets = {
            "categories": forms.CheckboxSelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = None

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if SoundEffect.objects.filter(name=name).exists():
            raise ValidationError(f"Sound Effect with name {name} already exists")
        return name

    def clean_tenor_url(self):
        if self.cleaned_data["tenor_url"] and not self.cleaned_data["tenor_url"].startswith("https://tenor.com/view/"):
            raise ValidationError("Does not look like a valid tenor url",
                                  params={"tenor_url": self.cleaned_data["tenor_url"]})
        return self.cleaned_data["tenor_url"]

    def clean(self):
        # Download video
        if "yt_url" not in self.cleaned_data or "name" not in self.cleaned_data:
            return
        try:
            cached_stream = utils.get_stream(self.cleaned_data["yt_url"])
            path = cached_stream.file.path
        except YtException as exec:
            raise ValidationError("Something wrong with the youtube url?") from exec
        start_ms = self.cleaned_data.get("start_ms")
        end_ms = self.cleaned_data.get("end_ms")
        name = self.cleaned_data["name"]
        # If start and end ms exist. Replace file with clipped version
        if start_ms is not None and end_ms is not None:
            if end_ms <= start_ms:
                raise ValidationError("End time has to be bigger than start time")
            clip_data = utils.extract_clip_from_file(path, start_ms, end_ms)
            size = sys.getsizeof(clip_data)
            file = InMemoryUploadedFile(clip_data, "file", name, None, size, None)
        else:
            size = os.path.getsize(path)
            ytaudio = open(path, 'rb')
            file = InMemoryUploadedFile(ytaudio, "file", ytaudio.name, None, size, None)
        self.cleaned_data["file"] = file
        self.files["sound_effect"] = file
        self.instance.file = file
        if not self.cleaned_data.get("categories"):
            self.cleaned_data["categories"] = [Category.objects.get(name="No category").id]

    def save(self, commit=True):
        sound_effect = super().save(commit)
        if self.cleaned_data.get("tenor_url"):
            sound_effect.gifs.create(url=self.cleaned_data["tenor_url"])
        return sound_effect


class SoundEffectFilter(forms.Form):

    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False,
                                                widget=forms.CheckboxSelectMultiple)
    categoryless = forms.BooleanField(label="Include sound effects without category", required=False)

    favourite_list = forms.ModelMultipleChoiceField(queryset=Favourites.objects.filter(owner__isnull=True),
                                                    required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, user, *args, **kwargs):
        kwargs["prefix"] = "filter"
        super().__init__(*args, **kwargs)
        if user:
            self.fields["favourite_list"].queryset = user.favourite_lists.all()
