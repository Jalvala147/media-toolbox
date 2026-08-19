"""Utilidades para listar y filtrar archivos."""

from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac", ".wma", ".opus"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".m4v", ".mpeg", ".mpg"}
MEDIA_EXTS = IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS


def normalize_extension(extension_filter: str | None) -> str | None:
    if not extension_filter:
        return None
    ext = extension_filter.strip().lower()
    if not ext:
        return None
    return ext if ext.startswith(".") else f".{ext}"


def unique_path(path: str | Path) -> Path:
    path = Path(path)
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def collect_files(
    paths: list[str] | str | Path,
    *,
    allowed_extensions: set[str] | None = None,
    extension_filter: str | None = None,
    recursive: bool = False,
    sort: bool = True,
) -> list[Path]:
    """Devuelve archivos regulares a partir de carpetas y/o rutas de archivo."""
    if isinstance(paths, (str, Path)):
        paths = [paths]

    ext_filter = normalize_extension(extension_filter)
    found: list[Path] = []
    seen: set[Path] = set()

    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        candidates: list[Path]
        if path.is_file():
            candidates = [path]
        elif recursive:
            candidates = [p for p in path.rglob("*") if p.is_file()]
        else:
            candidates = [p for p in path.iterdir() if p.is_file()]

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            suffix = candidate.suffix.lower()
            if ext_filter and suffix != ext_filter:
                continue
            if allowed_extensions and suffix not in allowed_extensions:
                continue
            seen.add(resolved)
            found.append(candidate)

    if sort:
        found.sort(key=lambda p: p.name.lower())
    return found
