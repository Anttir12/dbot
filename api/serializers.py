from rest_framework import serializers

from sounds import models


class SoundEffectSerializer(serializers.ModelSerializer):

    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = models.SoundEffect
        fields = ["id", "created_at", "name", "categories"]


class FavouritesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Favourites
        fields = ["id", "name", "sound_effects"]
