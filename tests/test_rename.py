from pathlib import Path

from core.files import collect_files, normalize_extension
from core.rename import apply_rename_plan, build_rename_plan, undo_rename_plan
from core.zip_files import rename_and_zip


def test_normalize_extension():
    assert normalize_extension("jpg") == ".jpg"
    assert normalize_extension(".PNG") == ".png"
    assert normalize_extension("  ") is None


def test_collect_files_filters_and_skips_dirs(tmp_path: Path):
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "b.png").write_bytes(b"b")
    (tmp_path / "c.txt").write_bytes(b"c")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "d.jpg").write_bytes(b"d")

    top = collect_files(tmp_path, extension_filter=".jpg")
    assert [p.name for p in top] == ["a.jpg"]

    nested = collect_files(tmp_path, extension_filter=".jpg", recursive=True)
    assert sorted(p.name for p in nested) == ["a.jpg", "d.jpg"]


def test_rename_plan_and_undo(tmp_path: Path):
    (tmp_path / "zeta.jpg").write_bytes(b"z")
    (tmp_path / "alpha.jpg").write_bytes(b"a")
    (tmp_path / "keep.txt").write_bytes(b"k")

    plan = build_rename_plan(tmp_path, "foto", extension_filter=".jpg", start=1, padding=3)
    assert [item.destination.name for item in plan] == ["foto_001.jpg", "foto_002.jpg"]

    apply_rename_plan(plan)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["foto_001.jpg", "foto_002.jpg", "keep.txt"]
    assert (tmp_path / "foto_001.jpg").read_bytes() == b"a"

    undo_rename_plan(plan)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["alpha.jpg", "keep.txt", "zeta.jpg"]


def test_rename_avoids_in_batch_collisions(tmp_path: Path):
    (tmp_path / "foto_001.jpg").write_bytes(b"one")
    (tmp_path / "foto_002.jpg").write_bytes(b"two")

    plan = build_rename_plan(tmp_path, "foto", start=1, padding=3, sort_by="name")
    apply_rename_plan(plan)
    assert (tmp_path / "foto_001.jpg").read_bytes() == b"one"
    assert (tmp_path / "foto_002.jpg").read_bytes() == b"two"


def test_rename_and_zip_filters_extension():
    files = [
        {"name": "a.jpg", "content": b"1"},
        {"name": "b.png", "content": b"2"},
        {"name": "c.jpg", "content": b"3"},
    ]
    buffer = rename_and_zip(files, "img", extension_filter=".jpg", padding=2, start=5)
    import zipfile

    with zipfile.ZipFile(buffer) as zf:
        assert zf.namelist() == ["img_05.jpg", "img_06.jpg"]
