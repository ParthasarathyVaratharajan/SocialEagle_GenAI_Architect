import os
import subprocess
import tempfile
from pathlib import Path
from yt_dlp import YoutubeDL
from .utils import env

FFMPEG = env("FFMPEG_PATH", "ffmpeg")

def resolve_stream_url(youtube_url: str) -> str:
    # Extract a playable URL (best video) for lives/streams
    ydl_opts = {"format": "best", "noplaylist": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        # Prefer a direct URL if available
        return info.get("url", youtube_url)

def capture_clip(youtube_url: str, duration_seconds: int) -> Path:
    stream_url = resolve_stream_url(youtube_url)
    tmpdir = Path(tempfile.mkdtemp())
    outfile = tmpdir / "clip.mp4"

    cmd = [
        FFMPEG, "-y",
        "-i", stream_url,
        "-t", str(duration_seconds),
        "-c", "copy",
        str(outfile)
    ]
    subprocess.run(cmd, check=True)
    return outfile