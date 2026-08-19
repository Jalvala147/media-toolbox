from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from core.images import HEIF_SUPPORTED, convert_heic_to_jpeg, convert_image, resize_image, strip_image_metadata
from core.metadata import strip_metadata, wipe_all_metadata


def _jpeg_with_exif(path: Path) -> None:
    image = Image.new("RGB", (32, 24), (200, 10, 10))
    exif = image.getexif()
    exif[ExifBase.Make] = "MediaToolboxTest"
    image.save(path, format="JPEG", exif=exif)


def test_strip_image_metadata_removes_exif(tmp_path: Path):
    src = tmp_path / "photo.jpg"
    _jpeg_with_exif(src)
    assert Image.open(src).getexif().get(ExifBase.Make) == "MediaToolboxTest"

    dest = tmp_path / "photo_clean.jpg"
    strip_image_metadata(src, dest)
    cleaned = Image.open(dest)
    assert cleaned.getexif().get(ExifBase.Make) is None
    assert cleaned.size == (32, 24)


def test_resize_keeps_aspect_ratio(tmp_path: Path):
    src = tmp_path / "wide.png"
    Image.new("RGB", (200, 100), "blue").save(src)
    dest = tmp_path / "wide_small.png"
    resize_image(src, 50, 50, keep_aspect=True, dest=dest)
    assert Image.open(dest).size == (50, 25)


def test_convert_png_to_jpeg(tmp_path: Path):
    src = tmp_path / "alpha.png"
    Image.new("RGBA", (10, 10), (255, 0, 0, 128)).save(src)
    dest = convert_image(src, ".jpg")
    assert dest.suffix == ".jpg"
    assert dest.exists()
    assert Image.open(dest).mode == "RGB"


def test_wipe_all_metadata_removes_exif(tmp_path: Path):
    src = tmp_path / "gps.jpg"
    _jpeg_with_exif(src)
    dest = wipe_all_metadata(src, overwrite=False)
    assert dest.exists()
    assert Image.open(dest).getexif().get(ExifBase.Make) is None
    assert Image.open(src).getexif().get(ExifBase.Make) == "MediaToolboxTest"


def test_convert_heic_to_jpeg(tmp_path: Path):
    if not HEIF_SUPPORTED:
        pytest.skip("pillow-heif no está disponible")
    heic = tmp_path / "iphone.heic"
    Image.new("RGB", (20, 10), "purple").save(heic, format="HEIF")
    dest = convert_heic_to_jpeg(heic, quality=85)
    assert dest.suffix == ".jpg"
    assert dest.exists()
    assert Image.open(dest).size == (20, 10)


def test_strip_metadata_dispatcher_writes_copy(tmp_path: Path):
    src = tmp_path / "cam.jpg"
    _jpeg_with_exif(src)
    dest = strip_metadata(src, overwrite=False)
    assert dest != src
    assert dest.exists()
    assert src.exists()
    assert Image.open(dest).getexif().get(ExifBase.Make) is None
