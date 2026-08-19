"""Renombrado por lotes con vista previa y dos pasadas (evita colisiones)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from core.files import collect_files, normalize_extension

DEFAULT_PATTERN = "{name}_{num}{ext}"
VALID_PATTERNS = (
    "{name}_{num}{ext}",
    "{num}_{name}{ext}",
    "{original}_{num}{ext}",
    "{name}{ext}",
)


@dataclass(frozen=True)
class RenamePlanItem:
    source: Path
    destination: Path


def build_rename_plan(
    folder: str | Path,
    new_name: str,
    extension_filter: str | None = None,
    start: int = 1,
    padding: int = 3,
    sort_by: str = "name",
    pattern: str = DEFAULT_PATTERN,
    recursive: bool = False,
) -> list[RenamePlanItem]:
    if not new_name.strip():
        raise ValueError("El nombre base no puede estar vacío.")
    if start < 0:
        raise ValueError("El número inicial no puede ser negativo.")
    if padding < 1 or padding > 8:
        raise ValueError("El padding debe estar entre 1 y 8.")
    if pattern not in VALID_PATTERNS:
        raise ValueError(f"Patrón no válido. Usa uno de: {', '.join(VALID_PATTERNS)}")

    files = collect_files(
        str(folder),
        extension_filter=extension_filter,
        recursive=recursive,
    )
    if sort_by == "date":
        files.sort(key=lambda p: (p.stat().st_mtime, p.name.lower()))
    else:
        files.sort(key=lambda p: p.name.lower())

    plan: list[RenamePlanItem] = []
    counter = start
    for src in files:
        dest_name = pattern.format(
            name=new_name.strip(),
            num=str(counter).zfill(padding),
            ext=src.suffix,
            original=src.stem,
        )
        plan.append(RenamePlanItem(src, src.parent / dest_name))
        counter += 1

    destinations = [item.destination.resolve() for item in plan]
    if len(set(destinations)) != len(destinations):
        raise ValueError("El patrón genera nombres duplicados. Cambia el patrón o el padding.")
    return plan


def apply_rename_plan(plan: list[RenamePlanItem]) -> int:
    """Renombra en dos pasadas para no pisar archivos del mismo lote."""
    if not plan:
        return 0

    sources = {item.source.resolve() for item in plan}
    for item in plan:
        dest = item.destination.resolve()
        if dest.exists() and dest not in sources and dest != item.source.resolve():
            raise FileExistsError(f"Ya existe un archivo con el nombre destino: {item.destination.name}")

    mapping: list[tuple[Path, Path, Path]] = []
    try:
        for index, item in enumerate(plan):
            if item.source.resolve() == item.destination.resolve():
                continue
            temp = item.source.with_name(f".__mt_tmp_{index}_{os.getpid()}{item.source.suffix}")
            os.rename(item.source, temp)
            mapping.append((item.source, temp, item.destination))
        for _original, temp, dest in mapping:
            os.rename(temp, dest)
    except Exception:
        for original, temp, dest in mapping:
            if temp.exists():
                try:
                    os.rename(temp, original)
                except OSError:
                    pass
            elif dest.exists() and not original.exists():
                try:
                    os.rename(dest, original)
                except OSError:
                    pass
        raise
    return len(plan)


def rename_files(folder, new_name, extension_filter=None):
    """Compatibilidad con la versión 1.0."""
    plan = build_rename_plan(
        folder,
        new_name,
        extension_filter=normalize_extension(extension_filter),
    )
    return apply_rename_plan(plan)


def undo_rename_plan(plan: list[RenamePlanItem]) -> int:
    reversed_plan = [
        RenamePlanItem(source=item.destination, destination=item.source)
        for item in reversed(plan)
        if item.destination.exists()
    ]
    return apply_rename_plan(reversed_plan)
