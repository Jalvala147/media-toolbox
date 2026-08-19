"""Limpieza de metadatos para imagen, audio y video."""

from __future__ import annotations

import shutil
from pathlib import Path

from mutagen import File as MutagenFile

from core.files import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS
from core.images import output_image_path, strip_image_metadata
from core.media import strip_av_metadata


def _unique_copy(src: Path, label: str, output_dir: str | Path | None = None) -> Path:
    folder = Path(output_dir) if output_dir else src.parent
    dest = folder / f"{src.stem}{label}{src.suffix}"
    index = 2
    while dest.exists():
        dest = folder / f"{src.stem}{label}_{index}{src.suffix}"
        index += 1
    shutil.copy2(src, dest)
    return dest


def strip_audio_tags(path: str | Path) -> Path:
    path = Path(path)
    audio = MutagenFile(str(path))
    if audio is None:
        raise ValueError(f"No se pudo leer el audio: {path.name}")
    audio.delete()
    audio.save()
    return path


def strip_metadata(
    src: str | Path,
    *,
    overwrite: bool = False,
    output_dir: str | Path | None = None,
    deep: bool = False,
) -> Path:
    src = Path(src)
    suffix = src.suffix.lower()
    label = "_sin_metadatos"

    if suffix in IMAGE_EXTS:
        dest = src if overwrite else output_image_path(src, label, output_dir)
        return strip_image_metadata(src, dest)

    if suffix in AUDIO_EXTS:
        dest = src if overwrite else _unique_copy(src, label, output_dir)
        try:
            strip_audio_tags(dest)
        except Exception:
            if dest != src and dest.exists():
                dest.unlink()
            dest = strip_av_metadata(src, overwrite=overwrite, output_dir=output_dir, deep=deep)
        else:
            if deep:
                dest = strip_av_metadata(dest, overwrite=True, deep=True)
                try:
                    strip_audio_tags(dest)
                except Exception:
                    pass
        return dest

    if suffix in VIDEO_EXTS:
        return strip_av_metadata(src, overwrite=overwrite, output_dir=output_dir, deep=deep)

    raise ValueError(f"Tipo de archivo no soportado: {src.name}")


def wipe_all_metadata(
    src: str | Path,
    *,
    overwrite: bool = False,
    output_dir: str | Path | None = None,
) -> Path:
    """Borra EXIF, GPS, etiquetas, capítulos y metadatos de contenedor."""
    return strip_metadata(src, overwrite=overwrite, output_dir=output_dir, deep=True)
