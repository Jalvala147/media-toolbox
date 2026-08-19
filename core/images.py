"""Operaciones de imagen: metadatos, redimensionado y conversión."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.files import IMAGE_EXTS

_FORMAT_BY_EXT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".bmp": "BMP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".gif": "GIF",
}


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _open_still_image(src: Path) -> Image.Image:
    image = Image.open(src)
    if getattr(image, "is_animated", False) and getattr(image, "n_frames", 1) > 1:
        image.seek(0)
        image = image.copy()
    return image


def _prepare_for_format(image: Image.Image, fmt: str) -> Image.Image:
    if fmt == "JPEG":
        if image.mode in {"RGBA", "LA", "P"}:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        if image.mode != "RGB":
            return image.convert("RGB")
    return image


def _save_image(image: Image.Image, dest: Path, fmt: str, quality: int = 90) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    kwargs: dict = {}
    if fmt in {"JPEG", "WEBP"}:
        kwargs["quality"] = max(1, min(quality, 100))
        kwargs["optimize"] = True
    if fmt == "JPEG":
        kwargs["exif"] = b""
    if fmt == "PNG":
        kwargs["optimize"] = True
    tmp = dest.with_name(f".{dest.name}.tmp")
    try:
        image.save(tmp, format=fmt, **kwargs)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def strip_image_metadata(src: str | Path, dest: str | Path | None = None) -> Path:
    src = Path(src)
    dest = Path(dest) if dest else src
    fmt = _FORMAT_BY_EXT.get(dest.suffix.lower()) or Image.open(src).format or "PNG"
    with _open_still_image(src) as image:
        cleaned = Image.new(image.mode, image.size)
        pixels = (
            image.get_flattened_data()
            if hasattr(image, "get_flattened_data")
            else image.getdata()
        )
        cleaned.putdata(list(pixels))
        if image.mode == "P" and image.getpalette():
            cleaned.putpalette(image.getpalette())
        cleaned = _prepare_for_format(cleaned, fmt)
        _save_image(cleaned, dest, fmt)
    return dest


def resize_image(
    src: str | Path,
    width: int,
    height: int,
    *,
    keep_aspect: bool = True,
    dest: str | Path | None = None,
    quality: int = 90,
) -> Path:
    if width < 1 or height < 1:
        raise ValueError("El ancho y el alto deben ser mayores que 0.")
    src = Path(src)
    dest = Path(dest) if dest else src
    fmt = _FORMAT_BY_EXT.get(dest.suffix.lower(), "PNG")
    with _open_still_image(src) as image:
        work = image.copy()
        if keep_aspect:
            work.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            work = work.resize((width, height), Image.Resampling.LANCZOS)
        work = _prepare_for_format(work, fmt)
        _save_image(work, dest, fmt, quality=quality)
    return dest


def convert_image(
    src: str | Path,
    dest_ext: str,
    *,
    dest: str | Path | None = None,
    quality: int = 90,
) -> Path:
    src = Path(src)
    ext = dest_ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    if ext not in IMAGE_EXTS:
        raise ValueError(f"Extensión de imagen no soportada: {ext}")
    fmt = _FORMAT_BY_EXT[ext]
    dest = Path(dest) if dest else src.with_suffix(ext)
    with _open_still_image(src) as image:
        work = _prepare_for_format(image.copy(), fmt)
        _save_image(work, dest, fmt, quality=quality)
    return dest


def output_image_path(src: Path, suffix_label: str, output_dir: str | Path | None = None, new_ext: str | None = None) -> Path:
    folder = Path(output_dir) if output_dir else src.parent
    ext = new_ext if new_ext is not None else src.suffix
    return _unique_path(folder / f"{src.stem}{suffix_label}{ext}")
