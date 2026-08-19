from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from core.organize import apply_organize_plan, build_organize_plan, media_datetime


def _jpeg_dated(path: Path, stamp: str) -> None:
    image = Image.new("RGB", (8, 8), "green")
    exif = image.getexif()
    exif[ExifBase.DateTimeOriginal] = stamp
    image.save(path, format="JPEG", exif=exif)


def test_media_datetime_prefers_exif(tmp_path: Path):
    photo = tmp_path / "cam.jpg"
    _jpeg_dated(photo, "2021:07:15 09:30:00")
    taken = media_datetime(photo)
    assert taken == datetime(2021, 7, 15, 9, 30, 0)


def test_organize_plan_year_month(tmp_path: Path):
    photo = tmp_path / "playa.jpg"
    _jpeg_dated(photo, "2022:12:01 12:00:00")
    dest = tmp_path / "salida"
    plan = build_organize_plan([photo], dest, layout="year_month")
    assert len(plan) == 1
    assert plan[0].destination == dest / "2022" / "12" / "playa.jpg"


def test_apply_organize_copies(tmp_path: Path):
    photo = tmp_path / "foto.jpg"
    _jpeg_dated(photo, "2020:01:02 03:04:05")
    dest = tmp_path / "album"
    plan = build_organize_plan([photo], dest, layout="year_month_day")
    count = apply_organize_plan(plan, move=False)
    assert count == 1
    assert photo.exists()
    assert (dest / "2020" / "01" / "02" / "foto.jpg").exists()
