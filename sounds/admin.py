import redis
from django.conf import settings
from django.contrib import admin

from django import forms
from django.forms import widgets

from . import utils
from .models import SoundEffect, SoundEffectGif, AlternativeName, CachedStream, Category, Favourites, DiscordUser, \
    EventTriggeredSoundEffect, SoundEffectPlayHistory


class RangeInput(widgets.NumberInput):
    input_type = "range"


class SoundEffectForm(forms.ModelForm):

    volume_slider = forms.FloatField(label="", required=False, max_value=5, min_value=0.01, initial=1.00,
                                     help_text="Updates value on below volume input",
                                     widget=RangeInput(attrs={"step": "0.01"}))

    volume = forms.FloatField(label="Volume modifier", required=False, max_value=5, min_value=0.01, initial=1.00,
                              widget=widgets.NumberInput(attrs={"step": "0.01"}),
                              help_text="Value between 0.01 and 5. Click preview to listen before saving. "
                                        "1 = current volume")

    start_ms = forms.IntegerField(label="Start time (ms)", required=False,
                                  help_text="Change the start time of this clip. <b>THIS ACTION CANNOT BE UNDONE</b>")
    end_ms = forms.IntegerField(label="End time (ms)", required=False,
                                help_text="Change the end time of this clip. <b>THIS ACTION CANNOT BE UNDONE</b>")

    class Meta:
        model = SoundEffect
        fields = ("name", "file", "categories")


class SoundEffectAdmin(admin.ModelAdmin):
    form = SoundEffectForm
    list_display = ("name", "created_by", "created_at")
    readonly_fields = ("duration",)
    search_fields = ("name",)
    autocomplete_fields = ("categories",)
    list_filter = ("categories",)

    def duration(self, obj):
        return "{}ms".format(utils.get_duration_of_audio_file(obj.file.path))

    def save_model(self, request, obj: SoundEffect, form, change):
        super().save_model(request, obj, form, change)
        utils.modify_sound_effect(obj, volume_modifier=form.cleaned_data["volume"],
                                  start_ms=form.cleaned_data["start_ms"], end_ms=form.cleaned_data["end_ms"])


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class SoundEffectPlayHistoryAdmin(admin.ModelAdmin):
    list_display = ("played_at", "played_by", "sound_effect")
    readonly_fields = ("sound_effect", "played_by", "played_at")


class DiscordUserAdmin(admin.ModelAdmin):
    actions = ["make_bot_aware"]

    @admin.action(description="Push the data to redis so Bot knows what's up")
    def make_bot_aware(self, _request, _queryset):
        r = redis.StrictRedis.from_url(settings.BOT_REDIS_URL, decode_responses=True)
        r.delete("AUTO_JOIN_USERS")
        auto_join_users = [duser.user_id for duser in DiscordUser.objects.filter(auto_join=True)]
        if auto_join_users:
            r.sadd("AUTO_JOIN_USERS", *auto_join_users)


admin.site.register(Category, CategoryAdmin)
admin.site.register(SoundEffect, SoundEffectAdmin)
admin.site.register(SoundEffectGif)
admin.site.register(AlternativeName)
admin.site.register(CachedStream)
admin.site.register(Favourites)
admin.site.register(DiscordUser, DiscordUserAdmin)
admin.site.register(EventTriggeredSoundEffect)
admin.site.register(SoundEffectPlayHistory, SoundEffectPlayHistoryAdmin)
