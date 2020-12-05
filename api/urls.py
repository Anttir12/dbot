from django.urls import path
from django.views.generic import TemplateView
from rest_framework.authentication import SessionAuthentication
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views

urlpatterns = [
    path('openapi', get_schema_view(
        title="Dbot Soundboard",
        description="API for all things Dbot soundboard and maybe more some day",
        version="1.0.0",
        authentication_classes=[SessionAuthentication]
    ), name='openapi-schema'),
    path('swagger-ui', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),

    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    path('sound_effects', views.SoundEffectList.as_view(), name="api_sound_effects"),
    path('sound_effects/<int:pk>', views.SoundEffectDetail.as_view(), name="api_sound_effect"),
    path('sound_effects/<int:pk>/audio', views.SoundEffectAudio.as_view(), name="api_sound_effect_audio"),

    path('sound_effects/from_yt', views.SoundEffectFromYT.as_view(), name="sound_effect_from_yt"),

    path('category/<str:category_name>/sound_effects', views.SoundEffectsByCategory.as_view(),
         name="api_sound_effects_by_category"),

    path('favourites', views.FavouritesList.as_view(), name="favourites"),
    path('favourites/<int:pk>', views.FavouritesDetail.as_view(), name="favourites_detail"),
    path('favourites/<int:pk>/sound_effects', views.FavouritesSoundEffects.as_view(), name="favourites_sound_effects"),

    path('bot/play_sound/<int:pk>', views.BotPlaySound.as_view(), name="api_play_sound"),
]
