from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404, ListAPIView, ListCreateAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api import custom_permissions, serializers
from api.serializers import SoundEffectSerializer, FavouritesSerializer

from sounds import models, tasks, utils
from sounds.forms import SoundEffectUpload


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


class SoundEffectFromYT(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SoundEffectFromYTSerializer

    def get(self, request):
        """
        Returns preview of the clip taken from YT.
        Required query parameters: yt_url (str), name (str)
        Optional (but recommended!) parameters: start_ms(int), end_ms(int)
        :param request:
        :return:
        """
        form = SoundEffectUpload(request.GET)
        if form.is_valid():
            preview_file = form.instance.sound_effect.file.file
            return HttpResponse(preview_file, content_type="audio/ogg")
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):


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


class SoundEffectAudio(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """
        Returns audio file of the sound_effect with content_type audio/ogg. You can also provide optional volume
        query parameter (a float between 0.01 and 5). This can be used as a "preview" functionality for modifying the
        volume
        """
        sound_effect = get_object_or_404(models.SoundEffect, pk=pk)
        vol = request.query_params.get("volume")
        if vol:
            try:
                vol = float(vol)
                if not (0.009 <= vol <= 5.01):
                    raise serializers.serializers.ValidationError(f"Except vol to be float between 0.01 and 5 but "
                                                                  f"it was {vol}")
            except ValueError:
                raise serializers.serializers.ValidationError(f"Except vol to be float but it was {type(vol)}")
            file = utils.create_audio_file_modified_volume(sound_effect.sound_effect.path, vol)
        else:
            file = sound_effect.sound_effect.file
        response = HttpResponse(file, content_type="audio/ogg")
        return response

    def patch(self, request, pk):
        sound_effect = get_object_or_404(models.SoundEffect, pk=pk)
        vol_param = request.data.get("volume")
        try:
            vol = float(vol_param)
        except ValueError:
            raise serializers.serializers.ValidationError(f"Expected vol to be float but it was {type(vol_param)}")
        utils.modify_sound_effect_volume(sound_effect, vol)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavouritesList(ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavouritesSerializer

    def get_queryset(self):
        return models.Favourites.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FavouritesDetail(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, custom_permissions.FavouritesOwnerPermission]
    serializer_class = FavouritesSerializer
    queryset = models.Favourites.objects.all()


class FavouritesSoundEffects(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, _, pk):
        """
        Returns list of sound_effect in the favourites
        """
        favourites = get_object_or_404(models.Favourites, id=pk)
        serializer = SoundEffectSerializer(favourites.sound_effects.all(), many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """
        Add sound_effect to the favourites list

        Expected body: {"sound_effect_id": <int:id>}
        """
        favourites = get_object_or_404(models.Favourites, id=pk)
        sound_effect = self._get_sound_effect(request)
        favourites.sound_effects.add(sound_effect)
        serializer = FavouritesSerializer(favourites)
        return Response(serializer.data)

    def delete(self, request, pk):
        """
        Remove sound effect from the favourites list

        Expected body: {"sound_effect_id": <int:id>}
        """
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
        except ValueError as e:
            raise ValidationError("sound_effect_id has to be int") from e
        return get_object_or_404(models.SoundEffect, id=sound_effect_id)


class BotPlaySound(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """
        Request the bot to play sound effect
        """
        get_object_or_404(models.SoundEffect, pk=pk)
        override = True if request.POST.get("override") else False
        tasks.play_sound.delay(pk, override)
        return Response({"bot": "ok"})
