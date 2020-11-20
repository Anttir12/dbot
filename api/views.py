from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import SoundEffectSerializer, FavouritesSerializer

from sounds import models, tasks


class SoundEffectList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = request.query_params.getlist("categories")
        if categories:
            sound_effects = models.SoundEffect.objects.filter(categories__name__in=categories)
        else:
            sound_effects = models.SoundEffect.objects.all()
        serializer = SoundEffectSerializer(sound_effects, many=True)
        return Response(serializer.data)


class SoundEffectsByCategory(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category):
        sound_effects = models.SoundEffect.objects.filter(categories__name=category)
        serializer = SoundEffectSerializer(sound_effects, many=True)
        return Response(serializer.data)


class SoundEffectDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        sound_effect = get_object_or_404(models.SoundEffect, pk=pk)
        serializer = SoundEffectSerializer(sound_effect)
        return Response(serializer.data)


class SoundEffectAudio(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        sound_effect = get_object_or_404(models.SoundEffect, pk=pk)
        response = HttpResponse(sound_effect.sound_effect.file, content_type="audio/ogg")
        return response


class FavouritesList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        favourites = models.Favourites.objects.filter(owner=request.user)
        serializer = FavouritesSerializer(favourites, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FavouritesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavouritesDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        favourites = get_object_or_404(models.Favourites, id=pk)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)


class FavouritesSoundEffects(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        favourites = get_object_or_404(models.Favourites, id=pk)
        serializer = SoundEffectSerializer(favourites.sound_effects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        favourites = get_object_or_404(models.Favourites, id=pk)
        sound_effect = self._get_sound_effect(request)
        favourites.sound_effects.add(sound_effect)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)

    def delete(self, request, pk):
        favourites = get_object_or_404(models.Favourites, id=pk)
        sound_effect = self._get_sound_effect(request)
        favourites.sound_effects.remove(sound_effect)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)

    def _get_sound_effect(self, request):
        sound_effect_id = request.data.get("sound_effect_id")
        if sound_effect_id is None:
            raise ValidationError("sound_effect_id required")
        try:
            sound_effect_id = int(sound_effect_id)
        except TypeError as e:
            raise ValidationError("sound_effect_id has to be in") from e
        return get_object_or_404(models.SoundEffect, id=sound_effect_id)


class BotPlaySound(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        get_object_or_404(models.SoundEffect, pk=pk)
        override = True if request.POST.get("override") else False
        tasks.play_sound.delay(pk, override)
