import json
import os
import shutil
import subprocess
import logging
import sys
from io import BytesIO
from os.path import basename
from typing import Optional
from urllib.parse import urlparse, parse_qs

import magic
import pytube
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from pytube import Stream

from sounds.models import CachedStream, SoundEffect

logger = logging.getLogger(__name__)


class YtException(Exception):
    pass


def enough_disk_space_for_yt_stream(stream: Stream, path: str) -> bool:
    filesize = stream.filesize_approx
    _, _, free = shutil.disk_usage(path)
    return filesize * 1.1 < free


def extract_clip_from_file(path, start_ms, end_ms=None) -> BytesIO:
    return modify_sound_file(path, start_ms=start_ms, end_ms=end_ms)


def get_duration_of_audio_file(path):
    command = [
        settings.FFPROBE_PATH,
        "-i", path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format", '-hide_banner',
    ]
    output = subprocess.check_output(command)
    json_output = json.loads(output)
    duration = float(json_output["format"]["duration"])
    return duration * 1000


def create_modified_audio_in_memory_file(path: str, volume_modifier: Optional[float] = None,
                                         start_ms: Optional[int] = None, end_ms: Optional[int] = None,
                                         name: Optional[str] = None):
    if not name:
        name = basename(path)
    audio_bytes = modify_sound_file(path, volume_modifier=volume_modifier, start_ms=start_ms, end_ms=end_ms)
    size = sys.getsizeof(audio_bytes)
    file = InMemoryUploadedFile(audio_bytes, "sound_effect", name, None, size, None)
    return file


def modify_sound_file(path: str, volume_modifier: Optional[float] = None, start_ms: Optional[int] = None,
                      end_ms: Optional[int] = None) -> BytesIO:
    modifying_commands = []
    if start_ms or end_ms:
        if not start_ms:
            start_ms = 0
        if end_ms:
            duration = (end_ms - start_ms) / 1000
        else:
            audio_duration = get_duration_of_audio_file(path)
            duration = (audio_duration - start_ms) / 1000
        modifying_commands.extend([
            "-ss", f"{start_ms/1000}",  # Start offset
            "-t", f"{duration}",  # duration
        ])
    if volume_modifier:
        modifying_commands.extend([
            '-filter:a', 'volume={:.2f}'.format(volume_modifier),  # Use audio filter and change volume
        ])
    command = [
        settings.FFMPEG_PATH,  # FFMPEG path
        "-loglevel", "quiet",
        "-i", path,  # Input path
        *modifying_commands,
        "-f", "opus",  # format
        # "-acodec", "copy",  # audio codec -> copy from source
        "pipe:1"  # return raw data (don't make a new file)
    ]
    return BytesIO(subprocess.check_output(command))


def modify_sound_effect(sound_effect: SoundEffect, volume_modifier: Optional[float] = None,
                        start_ms: Optional[int] = None, end_ms: Optional[int] = None):
    file = create_modified_audio_in_memory_file(sound_effect.sound_effect.path, volume_modifier=volume_modifier,
                                                start_ms=start_ms, end_ms=end_ms, name=sound_effect.name)
    sound_effect.sound_effect = file
    sound_effect.save(update_fields=["sound_effect"])


def get_stream(yt_url) -> CachedStream:
    yt_id = get_yt_id_from_url(yt_url)
    cached_stream_query = CachedStream.objects.filter(yt_id=yt_id)
    cached_stream: CachedStream = cached_stream_query.first()
    if cached_stream:
        source = cached_stream
        logger.info("{} found in cache. Skipping download".format(yt_id))
    else:
        source = download_stream_and_cache_it(yt_url, yt_id)
    return source


def download_stream_and_cache_it(yt_url, yt_id) -> CachedStream:
    try:
        y_t = pytube.YouTube(yt_url)
    except Exception as broad_except:  # pylint: disable=broad-except
        raise YtException("Unable to load streams from {}".format(yt_url)) from broad_except

    filtered = y_t.streams.filter(audio_codec="opus").order_by('bitrate').desc().first()
    if not enough_disk_space_for_yt_stream(filtered, "/tmp"):
        raise YtException("Not enough disk space to download yt stream")
    source = filtered.download("/tmp/streams")
    title = filtered.title
    size = os.path.getsize(source)
    with open(source, 'rb') as ytaudio:
        ytaudio.seek(0)
        mime_type = magic.from_buffer(ytaudio.read(1024), mime=True)
        ytaudio.seek(0)
        file = InMemoryUploadedFile(ytaudio, "sound_effect", os.path.basename(source), mime_type, size, None)
        cached_stream = CachedStream(title=title, yt_id=yt_id, file=file, size=filtered.filesize_approx)
        cached_stream.save(remove_oldest_if_full=True)
        os.remove(source)
    return cached_stream


def get_yt_id_from_url(yt_url) -> str:
    parsed_url = urlparse(yt_url)
    if yt_url.startswith("https://www.youtube.com/"):
        yt_id = parse_qs(parsed_url.query)["v"][0]
    elif yt_url.startswith("https://youtu.be/"):
        yt_id = parsed_url.path[1:]
    else:
        raise YtException("URL not valid. URL has to start with <https://www.youtube.com/> or "
                          "<https://youtu.be/>")
    return yt_id
