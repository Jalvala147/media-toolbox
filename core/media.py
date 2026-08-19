"""Wrappers de ffmpeg para extraer audio, convertir y limpiar metadatos de video."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from core.files import AUDIO_EXTS, VIDEO_EXTS

AUDIO_CODECS = {
    ".mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
    ".wav": ["-c:a", "pcm_s16le"],
    ".aac": ["-c:a", "aac", "-b:a", "192k"],
    ".m4a": ["-c:a", "aac", "-b:a", "192k"],
    ".ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    ".flac": ["-c:a", "flac"],
}

VIDEO_CODECS = {
    ".mp4": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
    ".mov": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
    ".mkv": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"],
    ".webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus"],
    ".avi": ["-c:v", "mpeg4", "-q:v", "5", "-c:a", "libmp3lame", "-q:a", "4"],
}


class FFmpegNotFoundError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _run_ffmpeg(args: list[str]) -> None:
    if not ffmpeg_available():
        raise FFmpegNotFoundError(
            "No se encontró ffmpeg. Instálalo y vuelve a intentarlo "
            "(en Windows puedes usar https://ffmpeg.org/download.html)."
        )
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ffmpeg falló").strip()
        raise RuntimeError(detail.splitlines()[-1] if detail else "ffmpeg falló")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _normalize_ext(ext: str) -> str:
    value = ext.lower().strip()
    return value if value.startswith(".") else f".{value}"


def extract_audio(
    src: str | Path,
    dest_ext: str = ".mp3",
    output_dir: str | Path | None = None,
) -> Path:
    src = Path(src)
    ext = _normalize_ext(dest_ext)
    if ext not in AUDIO_CODECS:
        raise ValueError(f"Formato de audio no soportado: {ext}")
    folder = Path(output_dir) if output_dir else src.parent
    dest = _unique_path(folder / f"{src.stem}{ext}")
    _run_ffmpeg(["-i", str(src), "-vn", *AUDIO_CODECS[ext], str(dest)])
    return dest


def convert_media(
    src: str | Path,
    dest_ext: str,
    output_dir: str | Path | None = None,
) -> Path:
    src = Path(src)
    ext = _normalize_ext(dest_ext)
    folder = Path(output_dir) if output_dir else src.parent
    dest = _unique_path(folder / f"{src.stem}{ext}")

    if ext in AUDIO_CODECS:
        args = ["-i", str(src), "-vn", *AUDIO_CODECS[ext], str(dest)]
    elif ext in VIDEO_CODECS:
        args = ["-i", str(src), *VIDEO_CODECS[ext], str(dest)]
    else:
        raise ValueError(f"Formato de salida no soportado: {ext}")
    _run_ffmpeg(args)
    return dest


def strip_av_metadata(src: str | Path, overwrite: bool = False, output_dir: str | Path | None = None) -> Path:
    src = Path(src)
    suffix = src.suffix.lower()
    if suffix not in VIDEO_EXTS | AUDIO_EXTS:
        raise ValueError(f"No es un archivo de audio/video: {src.name}")

    folder = Path(output_dir) if output_dir else src.parent
    dest = src if overwrite else _unique_path(folder / f"{src.stem}_sin_metadatos{src.suffix}")
    tmp = src.with_name(f".{src.stem}_nometa_{src.suffix}")

    try:
        try:
            _run_ffmpeg(["-i", str(src), "-map_metadata", "-1", "-c", "copy", str(tmp)])
        except RuntimeError:
            if tmp.exists():
                tmp.unlink()
            _run_ffmpeg(["-i", str(src), "-map_metadata", "-1", str(tmp)])
        if overwrite:
            tmp.replace(src)
            return src
        tmp.replace(dest)
        return dest
    finally:
        if tmp.exists() and tmp != dest:
            tmp.unlink(missing_ok=True)


def supported_output_extensions(kind: str) -> list[str]:
    if kind == "audio":
        return list(AUDIO_CODECS)
    if kind == "video":
        return list(VIDEO_CODECS)
    return list(AUDIO_CODECS) + list(VIDEO_CODECS)
