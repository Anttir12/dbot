from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple

# Register your models here.
from ow.models import Hero, GameEvent, EventReaction
from sounds import models as sound_models


class EventReactionForm(forms.ModelForm):

    sound_effects = forms.ModelMultipleChoiceField(queryset=sound_models.SoundEffect.objects.all(),
                                                   widget=FilteredSelectMultiple("Sounds", is_stacked=False),
                                                   required=False)

    class Meta:
        model = EventReaction
        fields = ("event", "hero", "team", "created_by", "sound_effects")


class EventReactionAdmin(admin.ModelAdmin):
    form = EventReactionForm

    def get_ordering(self, request):
        return ['event', 'team', 'hero']


class HeroAdmin(admin.ModelAdmin):
    def get_ordering(self, request):
        return ['name']


class GameEventAdmin(admin.ModelAdmin):
    def get_ordering(self, request):
        return ['name']


admin.site.register(EventReaction, EventReactionAdmin)
admin.site.register(Hero, HeroAdmin)
admin.site.register(GameEvent, GameEventAdmin)
