from django.db import transaction
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404, ListAPIView, ListCreateAPIView, RetrieveAPIView, CreateAPIView, \
    UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api import custom_permissions, custom_renderers
from api.serializers import SoundEffectSerializer, FavouritesSerializer, SoundEffectFromYTSerializer, \
    PlayBotSoundSerializer, SoundEffectAudioSerializer, SoundEffectAudioPreviewSerializer, FavouritesMinimalSerializer

from sounds import models, utils


class SoundEffectList(ListAPIView):
    """
    Returns list of **all** sound effects
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectSerializer
    queryset = models.SoundEffect.objects.all()


class SoundEffectDetail(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectSerializer
    queryset = models.SoundEffect.objects.all()


class SoundEffectFromYT(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = SoundEffectFromYTSerializer(data=request.query_params, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            sound_effect = serializer.create_sound_effect(save=False)
            preview_file = sound_effect.sound_effect.file.file
            return HttpResponse(preview_file, content_type="audio/ogg")


class CreateSoundEffectFromYt(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectFromYTSerializer

    def get(self):
        serializer = self.serializer_class()
        if serializer.is_valid(raise_exception=True):
            sound_effect = serializer.create_sound_effect(save=False)
            preview_file = sound_effect.sound_effect.file.file
            return HttpResponse(preview_file, content_type="audio/ogg")


class CategoryList(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]


class SoundEffectsByCategory(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectSerializer
    lookup_url_kwarg = "category_name"

    def get_queryset(self):
        category_name = self.kwargs.get(self.lookup_url_kwarg)
        sound_effects = models.SoundEffect.objects.filter(categories__name=category_name)
        return sound_effects


class SoundEffectAudio(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectAudioSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @extend_schema(
        responses={(200, 'audio/ogg')}
    )
    def get(self, request, pk):
        """Returns audio file of the sound_effect with content_type audio/ogg. You can also provide optional volume
       query parameter (a float between 0.01 and 5). This can be used as a "preview" functionality for modifying the
       volume
       """
        serializer = self.serializer_class(data=request.query_params)
        sound_effect = get_object_or_404(models.SoundEffect, pk=pk)
        serializer.is_valid(raise_exception=True)
        vol = serializer.validated_data.get("volume")
        if vol:
            file = utils.create_audio_file_modified_volume(sound_effect.sound_effect.path, vol)
        else:
            file = sound_effect.sound_effect.file
        response = HttpResponse(file, content_type="audio/ogg")
        return response

    def get_object(self):
        return models.SoundEffect.objects.get(id=self.kwargs[self.lookup_field])


class SoundEffectAudioPreview(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [custom_renderers.AudioOGGRenderer]
    serializer_class = SoundEffectAudioPreviewSerializer

    def get_object(self):
        return models.SoundEffect.objects.get(id=self.kwargs[self.lookup_field])


class FavouritesList(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavouritesMinimalSerializer

    def get_queryset(self):
        return models.Favourites.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FavouritesDetail(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, custom_permissions.FavouritesOwnerPermission]
    serializer_class = FavouritesMinimalSerializer
    queryset = models.Favourites.objects.all()


class FavouritesSoundEffects(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """
        Returns list of sound_effect in the favourites
        """
        favourites = get_object_or_404(models.Favourites, id=pk, owner=request.user)
        serializer = SoundEffectSerializer(favourites.sound_effects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """
        Add sound_effect to the favourites list

        Expected body: {"sound_effects": <list[int:id]>}
        """
        favourites = get_object_or_404(models.Favourites, id=pk, owner=request.user)
        sound_effects = self._get_sound_effects(request)
        with transaction.atomic():
            for sound_effect in sound_effects:
                favourites.sound_effects.add(sound_effect)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)

    def delete(self, request, pk):
        """
        Remove sound effect from the favourites list

        Expected body: {"sound_effects": <list[int:id]>}
        """
        favourites = get_object_or_404(models.Favourites, id=pk)
        sound_effects = self._get_sound_effects(request)
        with transaction.atomic():
            for sound_effect in sound_effects:
                favourites.sound_effects.remove(sound_effect)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)

    def _get_sound_effects(self, request):
        sound_effects = request.data.get("sound_effects")
        if sound_effects is None:
            raise ValidationError("sound_effects required")
        if not isinstance(sound_effects, list):
            raise ValidationError("Expected list of sound effect IDs")
        return models.SoundEffect.objects.filter(id__in=sound_effects)


class BotPlaySound(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlayBotSoundSerializer
