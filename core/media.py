"""Wrappers de ffmpeg para extraer audio, convertir y limpiar metadatos de video."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from core.files import AUDIO_EXTS, VIDEO_EXTS, unique_path

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


WHATSAPP_PRESETS = {
    "720p": {"max_w": 1280, "max_h": 720, "crf": 26, "audio_k": 96, "fps": 30},
    "480p": {"max_w": 854, "max_h": 480, "crf": 28, "audio_k": 64, "fps": 24},
}


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
    dest = unique_path(folder / f"{src.stem}{ext}")
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
    dest = unique_path(folder / f"{src.stem}{ext}")

    if ext in AUDIO_CODECS:
        args = ["-i", str(src), "-vn", *AUDIO_CODECS[ext], str(dest)]
    elif ext in VIDEO_CODECS:
        args = ["-i", str(src), *VIDEO_CODECS[ext], str(dest)]
    else:
        raise ValueError(f"Formato de salida no soportado: {ext}")
    _run_ffmpeg(args)
    return dest


def parse_timestamp(value: str | float | int) -> float:
    """Convierte '90', '1:30' o '00:01:30' a segundos."""
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds < 0:
            raise ValueError("El tiempo no puede ser negativo.")
        return seconds
    text = str(value).strip().replace(",", ".")
    if not text:
        raise ValueError("El tiempo está vacío.")
    parts = text.split(":")
    try:
        if len(parts) == 1:
            seconds = float(parts[0])
        elif len(parts) == 2:
            seconds = int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        else:
            raise ValueError
    except ValueError as exc:
        raise ValueError("Usa segundos o un formato como 00:01:30.") from exc
    if seconds < 0:
        raise ValueError("El tiempo no puede ser negativo.")
    return seconds


def cut_clip(
    src: str | Path,
    start: str | float = 0,
    end: str | float | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    src = Path(src)
    start_s = parse_timestamp(start)
    folder = Path(output_dir) if output_dir else src.parent
    dest = unique_path(folder / f"{src.stem}_corte{src.suffix}")
    args = ["-i", str(src), "-ss", f"{start_s:.3f}"]
    if end is not None and str(end).strip() != "":
        end_s = parse_timestamp(end)
        if end_s <= start_s:
            raise ValueError("El tiempo final debe ser mayor que el inicial.")
        args += ["-to", f"{end_s:.3f}"]
    args += ["-map_metadata", "-1", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "128k", str(dest)]
    _run_ffmpeg(args)
    return dest


def join_clips(sources: list[str | Path], output_dir: str | Path | None = None) -> Path:
    clips = [Path(item) for item in sources]
    if len(clips) < 2:
        raise ValueError("Selecciona al menos dos videos para unir.")
    folder = Path(output_dir) if output_dir else clips[0].parent
    dest = unique_path(folder / f"{clips[0].stem}_unido.mp4")
    list_file = unique_path(folder / f".{clips[0].stem}_concat.txt")
    lines = []
    for clip in clips:
        escaped = clip.resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")
    try:
        try:
            _run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(dest)])
        except RuntimeError:
            if dest.exists():
                dest.unlink()
            _run_ffmpeg(
                [
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(list_file),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "20",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    str(dest),
                ]
            )
    finally:
        list_file.unlink(missing_ok=True)
    return dest


def compress_for_whatsapp(
    src: str | Path,
    preset: str = "720p",
    output_dir: str | Path | None = None,
) -> Path:
    if preset not in WHATSAPP_PRESETS:
        raise ValueError(f"Preset no válido. Usa: {', '.join(WHATSAPP_PRESETS)}")
    cfg = WHATSAPP_PRESETS[preset]
    src = Path(src)
    folder = Path(output_dir) if output_dir else src.parent
    dest = unique_path(folder / f"{src.stem}_whatsapp.mp4")
    vf = (
        f"scale={cfg['max_w']}:{cfg['max_h']}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"fps={cfg['fps']},format=yuv420p"
    )
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-profile:v",
            "main",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            str(cfg["crf"]),
            "-c:a",
            "aac",
            "-b:a",
            f"{cfg['audio_k']}k",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-movflags",
            "+faststart",
            "-map_metadata",
            "-1",
            str(dest),
        ]
    )
    return dest


def strip_av_metadata(
    src: str | Path,
    overwrite: bool = False,
    output_dir: str | Path | None = None,
    *,
    deep: bool = False,
) -> Path:
    src = Path(src)
    suffix = src.suffix.lower()
    if suffix not in VIDEO_EXTS | AUDIO_EXTS:
        raise ValueError(f"No es un archivo de audio/video: {src.name}")

    folder = Path(output_dir) if output_dir else src.parent
    dest = src if overwrite else unique_path(folder / f"{src.stem}_sin_metadatos{src.suffix}")
    tmp = unique_path(src.with_name(f".{src.stem}_nometa{src.suffix}"))
    extra = ["-map_metadata", "-1", "-map_chapters", "-1"]
    if deep:
        extra += ["-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]

    try:
        try:
            _run_ffmpeg(["-i", str(src), *extra, "-c", "copy", str(tmp)])
        except RuntimeError:
            if tmp.exists():
                tmp.unlink()
            _run_ffmpeg(["-i", str(src), *extra, str(tmp)])
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
