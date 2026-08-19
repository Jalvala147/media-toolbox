import shutil
import subprocess
from pathlib import Path

import pytest

from core.media import (
    compress_for_whatsapp,
    convert_media,
    cut_clip,
    extract_audio,
    extract_preview_frame,
    ffmpeg_available,
    format_timestamp,
    join_clips,
    parse_timestamp,
    probe_duration,
    rotate_video,
)
from core.metadata import strip_audio_tags, wipe_all_metadata

ffmpeg = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(not ffmpeg, reason="ffmpeg no está instalado")


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


def test_parse_timestamp_formats():
    assert parse_timestamp(90) == 90
    assert parse_timestamp("1:30") == 90
    assert parse_timestamp("00:01:30") == 90


def test_format_timestamp():
    assert format_timestamp(90) == "01:30"
    assert format_timestamp(3661) == "01:01:01"


@needs_ffmpeg
def test_preview_and_rotate(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    duration = probe_duration(video)
    assert duration > 0.5
    frame = extract_preview_frame(video, 0.2)
    assert frame[:2] == b"\xff\xd8"
    rotated = rotate_video(video, rotation="90")
    assert rotated.exists()
    assert rotated.suffix == ".mp4"


@needs_ffmpeg
def test_ffmpeg_is_detected():
    assert ffmpeg_available() is True


@needs_ffmpeg
def test_cut_and_join_clips(tmp_path: Path):
    first = tmp_path / "a.mp4"
    second = tmp_path / "b.mp4"
    _tiny_video(first)
    _tiny_video(second)
    cut = cut_clip(first, start=0.1, end=0.8)
    assert cut.exists()
    assert cut.stat().st_size > 0
    joined = join_clips([first, second])
    assert joined.exists()
    assert joined.suffix == ".mp4"


@needs_ffmpeg
def test_compress_for_whatsapp(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    compact = compress_for_whatsapp(video, preset="480p")
    assert compact.exists()
    assert compact.name.endswith("_whatsapp.mp4")


@needs_ffmpeg
def test_wipe_all_metadata_on_mp3(tmp_path: Path):
    audio = tmp_path / "song.mp3"
    _tiny_mp3(audio)
    from mutagen.id3 import ID3, TIT2
    from mutagen.mp3 import MP3

    tags = ID3()
    tags.add(TIT2(encoding=3, text="Titulo secreto"))
    tags.save(audio)
    cleaned = wipe_all_metadata(audio, overwrite=False)
    assert cleaned != audio
    tagged = MP3(cleaned)
    assert not tagged.tags or "TIT2" not in tagged.tags


@needs_ffmpeg
def test_extract_audio_creates_mp3(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    audio = extract_audio(video, dest_ext=".mp3")
    assert audio.exists()
    assert audio.suffix == ".mp3"
    assert audio.stat().st_size > 0


@needs_ffmpeg
def test_convert_video_to_mp4(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    _tiny_video(video)
    converted = convert_media(video, dest_ext=".mkv")
    assert converted.exists()
    assert converted.suffix == ".mkv"


@needs_ffmpeg
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
