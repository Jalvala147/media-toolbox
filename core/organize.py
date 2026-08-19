"""Organiza archivos de media en carpetas por fecha (EXIF o fecha del archivo)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from core.files import unique_path

EXIF_DATETIME_TAGS = (
    ExifBase.DateTimeOriginal,
    ExifBase.DateTimeDigitized,
    ExifBase.DateTime,
)
EXIF_IFD = 0x8769
LAYOUTS = ("year_month", "year_month_day")


@dataclass(frozen=True)
class OrganizeItem:
    source: Path
    destination: Path
    taken_at: datetime


def _parse_exif_datetime(raw: object) -> datetime | None:
    text = str(raw).strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d"):
        try:
            return datetime.strptime(text[:19] if len(text) >= 19 else text, fmt)
        except ValueError:
            continue
    return None


def read_exif_datetime(path: Path) -> datetime | None:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            candidates: list[object] = []
            for tag in EXIF_DATETIME_TAGS:
                value = exif.get(tag)
                if value:
                    candidates.append(value)
            try:
                ifd = exif.get_ifd(EXIF_IFD)
            except Exception:
                ifd = {}
            for tag in EXIF_DATETIME_TAGS:
                value = ifd.get(tag) if ifd else None
                if value:
                    candidates.append(value)
            for raw in candidates:
                parsed = _parse_exif_datetime(raw)
                if parsed:
                    return parsed
    except Exception:
        return None
    return None


def media_datetime(path: str | Path) -> datetime:
    path = Path(path)
    taken = read_exif_datetime(path)
    if taken:
        return taken
    return datetime.fromtimestamp(path.stat().st_mtime)


def folder_for_date(taken_at: datetime, layout: str) -> Path:
    if layout == "year_month_day":
        return Path(taken_at.strftime("%Y"), taken_at.strftime("%m"), taken_at.strftime("%d"))
    if layout != "year_month":
        raise ValueError("Usa year_month o year_month_day.")
    return Path(taken_at.strftime("%Y"), taken_at.strftime("%m"))


def build_organize_plan(
    files: list[str | Path],
    dest_root: str | Path,
    layout: str = "year_month",
) -> list[OrganizeItem]:
    root = Path(dest_root)
    plan: list[OrganizeItem] = []
    used: set[Path] = set()
    for raw in files:
        source = Path(raw)
        taken_at = media_datetime(source)
        dest = root / folder_for_date(taken_at, layout) / source.name
        while dest.resolve() in used or (dest.exists() and dest.resolve() != source.resolve()):
            dest = dest.with_name(f"{dest.stem}_{len(used) + 2}{dest.suffix}")
        used.add(dest.resolve())
        plan.append(OrganizeItem(source=source, destination=dest, taken_at=taken_at))
    return plan


def apply_organize_plan(plan: list[OrganizeItem], *, move: bool = False) -> int:
    count = 0
    for item in plan:
        if item.source.resolve() == item.destination.resolve():
            continue
        item.destination.parent.mkdir(parents=True, exist_ok=True)
        dest = unique_path(item.destination) if item.destination.exists() else item.destination
        if move:
            shutil.move(str(item.source), str(dest))
        else:
            shutil.copy2(item.source, dest)
        count += 1
    return count
