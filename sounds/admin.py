from django.contrib import admin

# Register your models here.
from django import forms
from django.forms import widgets

from . import utils
from .models import SoundEffect, SoundEffectGif, AlternativeName, CachedStream, Category, Favourites, DiscordUser, \
    EventTriggeredSoundEffect, OwEventSoundEffect, SoundEffectPlayHistory


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

    class Meta:
        model = SoundEffect
        fields = ("name", "sound_effect", "categories")


class SoundEffectAdmin(admin.ModelAdmin):
    form = SoundEffectForm
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name",)
    autocomplete_fields = ("categories",)
    list_filter = ("categories",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        volume = form.cleaned_data.get("volume")
        if volume and volume != 1.0:  # Skip if this has no effect
            utils.modify_sound_effect_volume(obj, form.cleaned_data["volume"])


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class SoundEffectPlayHistoryAdmin(admin.ModelAdmin):
    list_display = ("played_at", "played_by", "sound_effect")
    readonly_fields = ("sound_effect", "played_by", "played_at")


admin.site.register(Category, CategoryAdmin)
admin.site.register(SoundEffect, SoundEffectAdmin)
admin.site.register(SoundEffectGif)
admin.site.register(AlternativeName)
admin.site.register(CachedStream)
admin.site.register(Favourites)
admin.site.register(DiscordUser)
admin.site.register(EventTriggeredSoundEffect)
admin.site.register(OwEventSoundEffect)
admin.site.register(SoundEffectPlayHistory, SoundEffectPlayHistoryAdmin)
