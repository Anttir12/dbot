from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

# Register your models here.
from stt.models import SttReaction
from sounds import models as sound_models


class SttReactionForm(forms.ModelForm):

    sound_effects = forms.ModelMultipleChoiceField(queryset=sound_models.SoundEffect.objects.all(),
                                                   widget=FilteredSelectMultiple("Sounds", is_stacked=False),
                                                   required=True)

    class Meta:
        model = SttReaction
        fields = ("name", "active", "cooldown", "data", "sound_effects")


class SttReactionAdmin(admin.ModelAdmin):
    form = SttReactionForm
    pass


admin.site.register(SttReaction, SttReactionAdmin)
