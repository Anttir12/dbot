import os
import sys

from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException

from bot import dbot_skills
from sounds import models, utils
from sounds.utils import YtException
from ow import models as ow_models


class SoundEffectSerializer(serializers.ModelSerializer):

    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="username")
    my_total_play_count = serializers.IntegerField(read_only=True)
    my_play_count_month = serializers.IntegerField(read_only=True)
    play_count_month = serializers.IntegerField(read_only=True)
    total_play_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.SoundEffect
        fields = ["id", "created_at", "created_by", "name", "my_total_play_count", "my_play_count_month",
                  "play_count_month", "total_play_count", "categories"]


class SoundEffectFromYTSerializer(serializers.ModelSerializer):
    name = serializers.CharField(label="Name", required=True, write_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="username")
    yt_url = serializers.CharField(label="YouTube URL", max_length=200, required=True, write_only=True)
    start_ms = serializers.IntegerField(label="Start time (ms)", required=False, write_only=True)
    end_ms = serializers.IntegerField(label="End time (ms)", required=False, write_only=True)

    class Meta:
        model = models.SoundEffect
        fields = ("id", "created_at", "created_by", "name", "yt_url", "categories", "start_ms", "end_ms")

    def validate_name(self, value):
        if (models.SoundEffect.objects.filter(name=value).exists() or
                models.AlternativeName.objects.filter(name=value).exists()):
            raise ValidationError(f"Sound Effect with name {value} already exists")
        return value

    def validate_yt_url(self, value):
        try:
            utils.get_yt_id_from_url(value)
        except YtException as yte:
            raise ValidationError(str(yte)) from yte
        return value

    def validate(self, attrs):
        start_ms = attrs.get("start_ms")
        end_ms = attrs.get("end_ms")
        attrs["start_ms"] = start_ms if start_ms else None  # Convert "" and 0 to None
        attrs["end_ms"] = end_ms if end_ms else None  # Convert "" and 0 to None
        # If start and end ms exist. Replace file with clipped version
        if attrs["start_ms"] is not None and attrs["end_ms"] is not None:
            if attrs["end_ms"] <= attrs["start_ms"]:
                raise ValidationError("End time has to be bigger than start time")
        return attrs

    def create_sound_effect(self, validated_data=None, save=True):
        if not validated_data:
            validated_data = self.validated_data
        try:
            cached_stream = utils.get_stream(validated_data["yt_url"])
            path = cached_stream.file.path
        except YtException as ex:
            raise APIException(str(ex)) from ex
        if validated_data.get("start_ms") or validated_data.get("end_ms"):
            clip_data = utils.extract_clip_from_file(path, validated_data.get("start_ms"), validated_data.get("end_ms"))
            size = sys.getsizeof(clip_data)
            file = InMemoryUploadedFile(clip_data, "file", validated_data["name"], None, size, None)
        else:
            size = os.path.getsize(path)
            ytaudio = open(path, 'rb')
            file = InMemoryUploadedFile(ytaudio, "file", ytaudio.name, None, size, None)
        user = self.context["request"].user
        instance = models.SoundEffect(name=validated_data["name"], file=file, created_by=user)
        if save:
            with transaction.atomic():
                instance.save()
                if validated_data.get("categories"):
                    for category in validated_data["categories"]:
                        instance.categories.add(category)
                else:
                    default_category = models.Category.objects.get(name="No category")
                    instance.categories.add(default_category)
        return instance

    def create(self, validated_data):
        instance = self.create_sound_effect(validated_data, save=True)
        return instance


class MinimalSoundEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SoundEffect
        fields = ["id", "name"]


class FavouritesMinimalSerializer(serializers.ModelSerializer):
    sound_effects = MinimalSoundEffectSerializer(many=True, read_only=True)

    class Meta:
        model = models.Favourites
        fields = ["id", "name", "sound_effects"]


class FavouritesSerializer(serializers.ModelSerializer):
    sound_effects = SoundEffectSerializer(many=True, read_only=True)

    class Meta:
        model = models.Favourites
        fields = ["id", "name", "sound_effects"]

    def validate(self, attrs):
        owner = self.context["request"].user
        name = attrs.get("name")
        if self.Meta.model.objects.filter(owner=owner, name=name).exists():
            raise serializers.ValidationError(f'Favourites list for owner "{owner}" with name "{name}" already exists')
        return attrs

    def validate_sound_effects(self, value):
        if not models.SoundEffect.objects.filter(name=value).exists():
            raise ValidationError('Unable to find sound effect "{}"'.format(value))
        return value

    def create(self, validated_data):
        sound_effect_names = validated_data.pop("sound_effects", [])
        with transaction.atomic():
            instance = super().create(validated_data)
            for sound_effect_name in sound_effect_names:
                sound_effect = models.SoundEffect.objects.get(name=sound_effect_name)
                instance.sound_effects.add(sound_effect)
        return instance


class SoundEffectAudioSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(required=False, max_value=10.00, min_value=0.01)
    start_ms = serializers.IntegerField(required=False, min_value=0)
    end_ms = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="username")
    categories = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = models.SoundEffect
        fields = ("id", "created_at", "created_by", "categories", "volume", "start_ms", "end_ms")

    def update(self, instance, validated_data):
        utils.modify_sound_effect(instance, volume_modifier=validated_data["volume"],
                                  start_ms=validated_data["start_ms"], end_ms=validated_data["end_ms"])
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "volume" in self.validated_data:
            representation["volume"] = self.validated_data["volume"]
        return representation


class SoundEffectAudioPreviewSerializer(serializers.ModelSerializer):
    volume = serializers.FloatField(required=False, max_value=10.00, min_value=0.01, write_only=True)

    class Meta:
        model = models.SoundEffect
        fields = ("file", "volume")


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Category
        fields = ("id", "name", "color_code", "text_color_code")


class PlayBotSoundSerializer(serializers.Serializer):
    sound_effect_id = serializers.IntegerField(write_only=True, required=True)
    override = serializers.BooleanField(write_only=True, required=True)
    bot = serializers.CharField(read_only=True)

    def create(self, validated_data):
        user = self.context["request"].user
        sound_effect = models.SoundEffect.objects.get(id=validated_data["sound_effect_id"])
        played = async_to_sync(dbot_skills.play_sound)(sound_effect, override=validated_data["override"])
        if played:
            models.SoundEffectPlayHistory.create_record(sound_effect=sound_effect, played_by=user)
        return {"bot": "ok"}

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def validate_sound_effect_id(self, value):
        if not models.SoundEffect.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"SoundEffect with id {value} does not exist")
        return value


class PlayYtSerializer(serializers.Serializer):
    yt_url = serializers.CharField(label="YT URL", max_length=200, required=True, write_only=True)
    volume = serializers.FloatField(required=False, max_value=5.00, min_value=0.01, write_only=True, allow_null=True)

    def create(self, validated_data):
        async_to_sync(dbot_skills.play_from_yt_url)(yt_url=validated_data["yt_url"],
                                                    volume=validated_data.get("volume"))
        return {"bot": "ok"}

    def update(self, instance, validated_data):
        raise NotImplementedError()

    def validate_yt_url(self, value):
        try:
            utils.get_yt_id_from_url(value)
        except YtException as yte:
            raise ValidationError(str(yte)) from yte
        return value


class OwEventReactionSerializer(serializers.ModelSerializer):
    override = serializers.BooleanField(write_only=True, required=False, default=True)
    hero = serializers.SlugRelatedField(write_only=True, slug_field="name", queryset=ow_models.Hero.objects.all(),
                                        required=False)
    event = serializers.SlugRelatedField(write_only=True, slug_field="name", queryset=ow_models.GameEvent.objects.all())
    team = serializers.ChoiceField(write_only=True, choices=ow_models.Team.choices, required=False)
    event_triggered = serializers.BooleanField(read_only=True)

    class Meta:
        model = ow_models.EventReaction
        fields = ("hero", "event", "team", "override", "event_triggered")

    def create(self, validated_data):
        hero = validated_data.get("hero")
        event = validated_data.get("event")
        team = validated_data.get("team")
        success = async_to_sync(dbot_skills.ow_event)(hero, event, team, validated_data["override"])
        return {"event_triggered": success}
