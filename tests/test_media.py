import shutil
import subprocess
from pathlib import Path

import pytest

from core.media import convert_media, extract_audio, ffmpeg_available
from core.metadata import strip_audio_tags

ffmpeg = shutil.which("ffmpeg")

pytestmark = pytest.mark.skipif(not ffmpeg, reason="ffmpeg no está instalado")


def _tiny_video(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=160x120:rate=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )


def _tiny_mp3(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            "-c:a",
            "libmp3lame",
            str(path),
        ],
        check=True,
    )


def test_ffmpeg_is_detected():
    assert ffmpeg_available() is True


def test_extract_audio_creates_mp3(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    audio = extract_audio(video, dest_ext=".mp3")
    assert audio.exists()
    assert audio.suffix == ".mp3"
    assert audio.stat().st_size > 0


def test_convert_video_to_mp4(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    converted = convert_media(video, dest_ext=".mkv")
    assert converted.exists()
    assert converted.suffix == ".mkv"


def test_strip_audio_tags(tmp_path: Path):
    audio = tmp_path / "song.mp3"
    _tiny_mp3(audio)
    from mutagen.id3 import ID3, TIT2
    from mutagen.mp3 import MP3

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Titulo secreto"))
    tags.save(audio)
    assert MP3(audio).tags.get("TIT2").text[0] == "Titulo secreto"

    strip_audio_tags(audio)
    tagged = MP3(audio)
    assert not tagged.tags or "TIT2" not in tagged.tags
