from django.contrib import admin

# Register your models here.
from .models import SoundEffect, SoundEffectGif, AlternativeName


admin.site.register(SoundEffect)
admin.site.register(SoundEffectGif)
admin.site.register(AlternativeName)
