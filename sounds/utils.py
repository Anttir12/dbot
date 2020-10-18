import shutil
import subprocess
from io import BytesIO

from django.conf import settings
from pytube import Stream


def enough_disk_space_for_yt_stream(stream: Stream, path: str):
    filesize = stream.filesize_approx
    _, _, free = shutil.disk_usage(path)
    return filesize * 1.1 < free


def extract_clip_from_file(path, start_ms, end_ms) -> BytesIO:
    duration = (end_ms - start_ms) / 1000
    command = [
        settings.FFMPEG_PATH,  # FFMPEG path
        "-i", path,  # Input path
        "-ss", f"{start_ms/1000}",  # Start offset
        "-t", f"{duration}",  # duration
        "-f", "opus",  # format
        "-acodec", "copy",  # audio codec -> copy from source
        "pipe:1"  # return raw data (don't make a file)
    ]
    return BytesIO(subprocess.check_output(command))
