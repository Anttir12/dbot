from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views

app_name = "api"
urlpatterns = [
    # Schema and documentation
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('schema/redoc', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),

    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    path('token/ws', views.WebsocketTokenView.as_view(), name='websocket_token'),

    path('sound_effects', views.SoundEffectList.as_view(), name="sound_effects"),
    path('sound_effects/<int:pk>', views.SoundEffectDetail.as_view(), name="sound_effect"),
    path('sound_effects/<int:pk>/audio', views.SoundEffectAudio.as_view(), name="sound_effect_audio"),

    path('sound_effects/from_yt', views.CreateSoundEffectFromYt.as_view(), name="sound_effect_from_yt"),

    path('categories', views.CategoryList.as_view(), name="categories"),
    path('categories/<str:category_name>/sound_effects', views.SoundEffectsByCategory.as_view(),
         name="sound_effects_by_category"),

    path('favourites', views.FavouritesList.as_view(), name="favourites"),
    path('favourites/<int:pk>', views.FavouritesDetail.as_view(), name="favourites_detail"),
    path('favourites/<int:pk>/sound_effects', views.FavouritesSoundEffects.as_view(), name="favourites_sound_effects"),

    path('bot/play_sound', views.BotPlaySound.as_view(), name="play_sound"),
    path('bot/discord_event/welcome', views.DiscordEventWelcome.as_view(), name="discord_event_welcome"),
    path('bot/discord_event/greetings', views.DiscordEventGreetings.as_view(), name="discord_event_greetings"),
    path('bot/play_yt', views.BotPlayYt.as_view(), name="play_yt"),
    path('bot/ow_event', views.OwEvent.as_view(), name="ow_event"),
]
