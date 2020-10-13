import shutil

from pytube import Stream


def enough_disk_space_for_yt_stream(stream: Stream, path: str):
    filesize = stream.filesize_approx
    _, _, free = shutil.disk_usage(path)
    return filesize * 1.1 < free
