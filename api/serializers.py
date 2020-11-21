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

    def validate(self, attrs):
        owner = self.context["request"].user
        name = attrs.get("name")
        if self.Meta.model.objects.filter(owner=owner, name=name).exists():
            raise serializers.ValidationError(f'Favourites list for owner "{owner}" with name "{name}" already exists')
        return attrs
