from django.contrib import admin

# Register your models here.
from stt.models import SttReaction


class SttReactionAdmin(admin.ModelAdmin):
    pass

admin.site.register(SttReaction, SttReactionAdmin)
