from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views

urlpatterns = [
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    path('sound_effects', views.SoundEffectList.as_view(), name="api_sound_effects"),
    path('sound_effects/category/<str:category>', views.SoundEffectsByCategory.as_view(),
         name="api_sound_effects_by_category"),
    path('sound_effects/<int:pk>', views.SoundEffectDetail.as_view(), name="api_sound_effect"),
    path('sound_effects/<int:pk>/audio', views.SoundEffectAudio.as_view(), name="api_sound_effect_audio"),

    path('favourites', views.FavouritesList.as_view(), name="favourites"),
    path('favourites/<int:pk>', views.FavouritesDetail.as_view(), name="favourites_detail"),
    path('favourites/<int:pk>/sound_effects', views.FavouritesSoundEffects.as_view(), name="favourites_sound_effects"),

    path('bot/play_sound/<int:pk>', views.BotPlaySound.as_view(), name="api_play_sound"),
]
