"""Media Toolbox — caja de herramientas para archivos de imagen, audio y video."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import flet as ft

from core.files import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS, collect_files, normalize_extension
from core.images import convert_image, output_image_path, resize_image
from core.media import compress_for_whatsapp, convert_media, cut_clip, extract_audio, ffmpeg_available, join_clips
from core.metadata import wipe_all_metadata
from core.organize import apply_organize_plan, build_organize_plan
from core.rename import apply_rename_plan, build_rename_plan, undo_rename_plan

VERSION = "2.1"
CYAN = ft.Colors.CYAN_400
CARD_BG = "#111827"
PAGE_BG = "#0b1220"
MUTED = ft.Colors.BLUE_GREY_200

AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
VIDEO_FORMATS = [".mp4", ".mkv", ".webm", ".mov"]
IMAGE_FORMATS = [".jpg", ".png", ".webp", ".bmp"]


def open_path(path: str | Path) -> None:
    target = str(Path(path))
    try:
        if sys.platform == "win32":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target])
        else:
            subprocess.Popen(["xdg-open", target])
    except OSError:
        pass


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


class MediaToolboxApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.picker = ft.FilePicker()
        self.body = ft.Container(expand=True, padding=24)
        self.status = ft.Text("", size=14, selectable=True)
        self.progress = ft.ProgressBar(value=0, color=CYAN, bgcolor="#1f2937", visible=False)
        self.selected: list[str] = []
        self.last_rename_plan = None
        self._busy = False

        page.title = "Media Toolbox"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = PAGE_BG
        page.padding = 0
        page.window.width = 820
        page.window.height = 860
        page.window.min_width = 640
        page.window.min_height = 700
        page.services.append(self.picker)
        page.add(
            ft.Column(
                [
                    self._header(),
                    self.body,
                ],
                expand=True,
                spacing=0,
            )
        )
        self.show_home()

    def _header(self) -> ft.Control:
        return ft.Container(
            bgcolor="#030712",
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            content=ft.Row(
                [
                    ft.Text("Media Toolbox", size=22, weight=ft.FontWeight.BOLD, color=CYAN),
                    ft.Container(expand=True),
                    ft.Text(f"v{VERSION}", size=12, color=MUTED),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def set_view(self, content: ft.Control) -> None:
        self.body.content = content
        self.page.update()

    def notify(self, message: str, *, error: bool = False) -> None:
        self.status.value = message
        self.status.color = ft.Colors.RED_400 if error else ft.Colors.TEAL_300
        self.page.update()

    def set_busy(self, busy: bool, current: int = 0, total: int = 0) -> None:
        self._busy = busy
        self.progress.visible = busy or current > 0
        if total:
            self.progress.value = current / total
        else:
            self.progress.value = None if busy else 0
        self.page.update()

    def selected_label(self) -> str:
        if not self.selected:
            return "Ningún archivo o carpeta seleccionado"
        if len(self.selected) == 1:
            return self.selected[0]
        return f"{len(self.selected)} elementos seleccionados"

    def file_list(self, paths: list[Path], limit: int = 40) -> ft.Control:
        if not paths:
            return ft.Text("No hay archivos para procesar.", color=MUTED, size=13)
        items = [
            ft.Text(f"• {path.name}", size=13, color=ft.Colors.WHITE70)
            for path in paths[:limit]
        ]
        if len(paths) > limit:
            items.append(ft.Text(f"… y {len(paths) - limit} más", size=12, color=MUTED))
        return ft.Column(items, spacing=2, tight=True)

    def tool_scaffold(self, title: str, subtitle: str, children: list[ft.Control]) -> ft.Control:
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=CYAN,
                            tooltip="Volver",
                            on_click=lambda e: self.show_home(),
                        ),
                        ft.Column(
                            [
                                ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=CYAN),
                                ft.Text(subtitle, size=13, color=MUTED),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=ft.Colors.CYAN_900),
                *children,
                self.progress,
                self.status,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
        )

    def show_home(self) -> None:
        self.selected = []
        self.status.value = ""
        self.progress.visible = False
        cards = [
            self._home_card(
                "Renombrar archivos",
                "Lotes con vista previa, numeración y deshacer",
                ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
                self.show_rename,
            ),
            self._home_card(
                "Borrar toda la metadata",
                "Quita EXIF, GPS, etiquetas y capítulos",
                ft.Icons.DELETE_SWEEP,
                self.show_metadata,
            ),
            self._home_card(
                "Cortar / unir video",
                "Recorta por tiempo o junta varios clips",
                ft.Icons.CONTENT_CUT,
                self.show_cut_join,
            ),
            self._home_card(
                "Comprimir para WhatsApp",
                "MP4 liviano en 720p o 480p, listo para enviar",
                ft.Icons.CHAT,
                self.show_whatsapp,
            ),
            self._home_card(
                "Organizar por fecha",
                "Carpetas YYYY/MM según EXIF o fecha del archivo",
                ft.Icons.DATE_RANGE,
                self.show_organize,
            ),
            self._home_card(
                "Extraer audio",
                "Saca MP3, WAV u otro audio desde un video",
                ft.Icons.AUDIO_FILE,
                self.show_extract,
            ),
            self._home_card(
                "Convertir medios",
                "Cambia formato de video o audio con ffmpeg",
                ft.Icons.TRANSFORM,
                self.show_convert,
            ),
            self._home_card(
                "Imágenes",
                "Redimensiona, comprime o convierte JPG/PNG/WebP",
                ft.Icons.PHOTO_SIZE_SELECT_LARGE,
                self.show_images,
            ),
        ]
        self.set_view(
            ft.Column(
                [
                    ft.Text(
                        "Elige una herramienta",
                        size=18,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "Procesa archivos en tu computadora. Las operaciones pesadas usan ffmpeg.",
                        size=13,
                        color=MUTED,
                    ),
                    ft.ResponsiveRow(cards, spacing=14, run_spacing=14),
                    ft.Container(height=8),
                    ft.Text(
                        "Hecho por Jalvala  ·  ffmpeg recomendado para audio y video",
                        size=12,
                        color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
                    ),
                ],
                spacing=16,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        )

    def _home_card(self, title: str, subtitle: str, icon, on_click) -> ft.Control:
        return ft.Container(
            col={"xs": 12, "md": 6},
            content=ft.Container(
                bgcolor=CARD_BG,
                border_radius=16,
                padding=18,
                on_click=lambda e: on_click(),
                content=ft.Row(
                    [
                        ft.Container(
                            width=48,
                            height=48,
                            bgcolor="#164e63",
                            border_radius=12,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(icon, color=CYAN, size=26),
                        ),
                        ft.Column(
                            [
                                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(subtitle, size=12, color=MUTED),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        )

    def _selection_row(self, picker_kind: str, extensions: list[str] | None = None) -> tuple[ft.Text, ft.Control]:
        summary = ft.Text(self.selected_label(), size=13, color=MUTED, selectable=True)

        async def pick_files(e=None):
            file_type = ft.FilePickerFileType.CUSTOM if extensions else ft.FilePickerFileType.ANY
            files = await self.picker.pick_files(
                allow_multiple=True,
                dialog_title="Selecciona archivos",
                file_type=file_type,
                allowed_extensions=[ext.lstrip(".") for ext in extensions] if extensions else None,
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                self.page.update()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path(dialog_title="Selecciona una carpeta")
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                self.page.update()

        buttons = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
        ]
        if picker_kind in {"folder", "both"}:
            buttons.append(
                ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder)
            )
        return summary, ft.Row(buttons, wrap=True, spacing=10)

    def gather_files(
        self,
        allowed: set[str] | None = None,
        extension_filter: str | None = None,
        recursive: bool = False,
        sort: bool = True,
    ) -> list[Path]:
        return collect_files(
            self.selected,
            allowed_extensions=allowed,
            extension_filter=extension_filter,
            recursive=recursive,
            sort=sort,
        )

    def show_rename(self) -> None:
        self.selected = []
        self.status.value = ""
        name_input = ft.TextField(label="Nombre base", hint_text="vacaciones", expand=True)
        ext_input = ft.TextField(label="Filtrar extensión", hint_text=".jpg", width=180)
        start_input = ft.TextField(label="Desde", value="1", width=110)
        padding_input = ft.TextField(label="Cifras", value="3", width=110)
        pattern = ft.Dropdown(
            label="Patrón",
            value="{name}_{num}{ext}",
            options=[
                ft.DropdownOption(key="{name}_{num}{ext}", text="nombre_001.ext"),
                ft.DropdownOption(key="{num}_{name}{ext}", text="001_nombre.ext"),
                ft.DropdownOption(key="{original}_{num}{ext}", text="original_001.ext"),
            ],
            expand=True,
        )
        sort_by = ft.Dropdown(
            label="Ordenar por",
            value="name",
            options=[
                ft.DropdownOption(key="name", text="Nombre"),
                ft.DropdownOption(key="date", text="Fecha"),
            ],
            width=180,
        )
        recursive = ft.Checkbox(label="Incluir subcarpetas", value=False)
        preview_box = ft.Column(spacing=4)
        summary, buttons = self._selection_row("both")

        def refresh_preview(e=None):
            preview_box.controls.clear()
            if not self.selected:
                preview_box.controls.append(ft.Text("Selecciona una carpeta o archivos para ver la vista previa.", color=MUTED))
                self.page.update()
                return
            try:
                folder = self.selected[0]
                if Path(folder).is_file():
                    folder = str(Path(folder).parent)
                plan = build_rename_plan(
                    folder,
                    name_input.value or "archivo",
                    extension_filter=normalize_extension(ext_input.value),
                    start=parse_int(start_input.value, 1),
                    padding=parse_int(padding_input.value, 3),
                    sort_by=sort_by.value or "name",
                    pattern=pattern.value or "{name}_{num}{ext}",
                    recursive=bool(recursive.value),
                )
                if not plan:
                    preview_box.controls.append(ft.Text("No hay archivos que coincidan.", color=MUTED))
                else:
                    preview_box.controls.append(
                        ft.Text(f"{len(plan)} archivos:", color=CYAN, weight=ft.FontWeight.BOLD)
                    )
                    for item in plan[:30]:
                        preview_box.controls.append(
                            ft.Text(f"{item.source.name}  →  {item.destination.name}", size=12, color=ft.Colors.WHITE70)
                        )
                    if len(plan) > 30:
                        preview_box.controls.append(ft.Text(f"… y {len(plan) - 30} más", color=MUTED, size=12))
            except Exception as err:
                preview_box.controls.append(ft.Text(str(err), color=ft.Colors.RED_400))
            self.page.update()

        def run_rename(e=None):
            if self._busy:
                return
            if not self.selected:
                self.notify("Selecciona una carpeta o archivos.", error=True)
                return
            if not (name_input.value or "").strip():
                self.notify("Escribe un nombre base.", error=True)
                return
            folder = self.selected[0]
            if Path(folder).is_file():
                folder = str(Path(folder).parent)
            try:
                plan = build_rename_plan(
                    folder,
                    name_input.value.strip(),
                    extension_filter=normalize_extension(ext_input.value),
                    start=parse_int(start_input.value, 1),
                    padding=parse_int(padding_input.value, 3),
                    sort_by=sort_by.value or "name",
                    pattern=pattern.value or "{name}_{num}{ext}",
                    recursive=bool(recursive.value),
                )
                count = apply_rename_plan(plan)
                self.last_rename_plan = plan
                self.notify(f"Renombrados {count} archivos.")
                refresh_preview()
            except Exception as err:
                self.notify(f"Error: {err}", error=True)

        def undo(e=None):
            if not self.last_rename_plan:
                self.notify("No hay un renombrado reciente para deshacer.", error=True)
                return
            try:
                count = undo_rename_plan(self.last_rename_plan)
                self.last_rename_plan = None
                self.notify(f"Deshechos {count} cambios.")
                refresh_preview()
            except Exception as err:
                self.notify(f"No se pudo deshacer: {err}", error=True)

        for control in (name_input, ext_input, start_input, padding_input, pattern, sort_by, recursive):
            if hasattr(control, "on_change"):
                control.on_change = refresh_preview
            if hasattr(control, "on_select"):
                control.on_select = refresh_preview

        original_pick_note = summary

        async def pick_and_preview_files(e=None):
            files = await self.picker.pick_files(allow_multiple=True, dialog_title="Selecciona archivos")
            if files:
                paths = [f.path for f in files if f.path]
                if paths:
                    self.selected = [str(Path(paths[0]).parent)]
                    original_pick_note.value = self.selected_label()
                    refresh_preview()

        async def pick_and_preview_folder(e=None):
            path = await self.picker.get_directory_path(dialog_title="Selecciona una carpeta")
            if path:
                self.selected = [path]
                original_pick_note.value = self.selected_label()
                refresh_preview()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_and_preview_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_and_preview_folder),
        ]

        self.set_view(
            self.tool_scaffold(
                "Renombrar archivos",
                "Cambia el nombre de muchos archivos a la vez, con numeración y vista previa.",
                [
                    summary,
                    buttons,
                    ft.Row([name_input, ext_input], spacing=12),
                    ft.Row([pattern, sort_by, start_input, padding_input], spacing=12, wrap=True),
                    recursive,
                    ft.Row(
                        [
                            ft.FilledButton("Renombrar", icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, on_click=run_rename),
                            ft.TextButton("Vista previa", on_click=refresh_preview),
                            ft.TextButton("Deshacer último", icon=ft.Icons.UNDO, on_click=undo),
                        ],
                        wrap=True,
                    ),
                    ft.Container(
                        bgcolor=CARD_BG,
                        border_radius=12,
                        padding=16,
                        content=preview_box,
                    ),
                ],
            )
        )
        preview_box.controls.append(
            ft.Text("Selecciona una carpeta o archivos para ver la vista previa.", color=MUTED)
        )

    def show_metadata(self) -> None:
        self.selected = []
        self.status.value = ""
        overwrite = ft.Checkbox(label="Sobrescribir originales (sin copia)", value=False)
        recursive = ft.Checkbox(label="Incluir subcarpetas", value=False)
        summary, buttons = self._selection_row(
            "both",
            [ext.lstrip(".") for ext in sorted(IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS)],
        )
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS, recursive=bool(recursive.value))
            preview.controls = [self.file_list(files)]
            self.page.update()

        recursive.on_change = refresh

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[ext.lstrip(".") for ext in sorted(IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS)],
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def run(e=None):
            files = self.gather_files(IMAGE_EXTS | AUDIO_EXTS | VIDEO_EXTS, recursive=bool(recursive.value))
            self._run_batch(
                files,
                lambda path: wipe_all_metadata(path, overwrite=bool(overwrite.value)),
                empty="No hay imágenes, audio o video en la selección.",
                done_label="Metadata borrada",
            )

        self.set_view(
            self.tool_scaffold(
                "Borrar toda la metadata",
                "Elimina EXIF, GPS, etiquetas ID3, capítulos y metadatos de contenedor. Por defecto guarda una copia.",
                [
                    summary,
                    buttons,
                    ft.Row([overwrite, recursive], wrap=True),
                    ft.FilledButton("Borrar toda la metadata", icon=ft.Icons.DELETE_SWEEP, on_click=run),
                    preview,
                ],
            )
        )

    def show_extract(self) -> None:
        self.selected = []
        self.status.value = ""
        fmt = ft.Dropdown(
            label="Formato de audio",
            value=".mp3",
            options=[ft.DropdownOption(key=ext, text=ext.upper().lstrip(".")) for ext in AUDIO_FORMATS],
            width=220,
        )
        summary, buttons = self._selection_row("both", [ext.lstrip(".") for ext in VIDEO_EXTS | AUDIO_EXTS])
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(VIDEO_EXTS | AUDIO_EXTS)
            preview.controls = [self.file_list(files)]
            self.page.update()

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[ext.lstrip(".") for ext in sorted(VIDEO_EXTS | AUDIO_EXTS)],
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def run(e=None):
            if not ffmpeg_available():
                self.notify("Necesitas ffmpeg instalado para extraer audio.", error=True)
                return
            files = self.gather_files(VIDEO_EXTS | AUDIO_EXTS)
            self._run_batch(
                files,
                lambda path: extract_audio(path, dest_ext=fmt.value or ".mp3"),
                empty="Selecciona videos (o audio) para extraer.",
                done_label="Audio extraído",
            )

        self.set_view(
            self.tool_scaffold(
                "Extraer audio",
                "Crea un archivo de audio nuevo al lado del video original.",
                [
                    summary,
                    buttons,
                    fmt,
                    ft.FilledButton("Extraer audio", icon=ft.Icons.AUDIO_FILE, on_click=run),
                    preview,
                ],
            )
        )

    def show_convert(self) -> None:
        self.selected = []
        self.status.value = ""
        fmt = ft.Dropdown(
            label="Convertir a",
            value=".mp4",
            options=[
                ft.DropdownOption(key=ext, text=f"Video {ext.upper().lstrip('.')}")
                for ext in VIDEO_FORMATS
            ]
            + [
                ft.DropdownOption(key=ext, text=f"Audio {ext.upper().lstrip('.')}")
                for ext in AUDIO_FORMATS
            ],
            width=260,
        )
        summary, buttons = self._selection_row("both", [ext.lstrip(".") for ext in VIDEO_EXTS | AUDIO_EXTS])
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(VIDEO_EXTS | AUDIO_EXTS)
            preview.controls = [self.file_list(files)]
            self.page.update()

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[ext.lstrip(".") for ext in sorted(VIDEO_EXTS | AUDIO_EXTS)],
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def run(e=None):
            if not ffmpeg_available():
                self.notify("Necesitas ffmpeg instalado para convertir.", error=True)
                return
            files = self.gather_files(VIDEO_EXTS | AUDIO_EXTS)
            self._run_batch(
                files,
                lambda path: convert_media(path, dest_ext=fmt.value or ".mp4"),
                empty="Selecciona audio o video para convertir.",
                done_label="Archivos convertidos",
            )

        self.set_view(
            self.tool_scaffold(
                "Convertir medios",
                "Re-codifica a otro formato. El original no se borra.",
                [
                    summary,
                    buttons,
                    fmt,
                    ft.FilledButton("Convertir", icon=ft.Icons.TRANSFORM, on_click=run),
                    preview,
                ],
            )
        )

    def show_images(self) -> None:
        self.selected = []
        self.status.value = ""
        width_input = ft.TextField(label="Ancho máx.", value="1920", width=140)
        height_input = ft.TextField(label="Alto máx.", value="1080", width=140)
        quality_input = ft.TextField(label="Calidad (1-100)", value="85", width=160)
        keep_aspect = ft.Checkbox(label="Mantener proporción", value=True)
        fmt = ft.Dropdown(
            label="Convertir a (opcional)",
            value="same",
            options=[
                ft.DropdownOption(key="same", text="Mismo formato"),
                *[ft.DropdownOption(key=ext, text=ext.upper().lstrip(".")) for ext in IMAGE_FORMATS],
            ],
            width=220,
        )
        overwrite = ft.Checkbox(label="Sobrescribir originales", value=False)
        summary, buttons = self._selection_row("both", [ext.lstrip(".") for ext in IMAGE_EXTS])
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(IMAGE_EXTS)
            preview.controls = [self.file_list(files)]
            self.page.update()

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.IMAGE,
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def process_one(path: Path) -> Path:
            width = parse_int(width_input.value, 1920)
            height = parse_int(height_input.value, 1080)
            quality = parse_int(quality_input.value, 85)
            target_ext = None if fmt.value in (None, "same") else fmt.value
            if overwrite.value:
                dest = path.with_suffix(target_ext or path.suffix)
            else:
                dest = output_image_path(
                    path,
                    "_edit",
                    new_ext=target_ext or path.suffix,
                )
            resized = resize_image(
                path,
                width,
                height,
                keep_aspect=bool(keep_aspect.value),
                dest=dest,
                quality=quality,
            )
            if target_ext and dest.suffix.lower() != target_ext:
                return convert_image(resized, target_ext, dest=dest, quality=quality)
            return resized

        def run(e=None):
            files = self.gather_files(IMAGE_EXTS)
            self._run_batch(
                files,
                process_one,
                empty="Selecciona imágenes para redimensionar o convertir.",
                done_label="Imágenes procesadas",
            )

        self.set_view(
            self.tool_scaffold(
                "Imágenes",
                "Redimensiona por lote y, si quieres, cambia el formato o comprime la calidad.",
                [
                    summary,
                    buttons,
                    ft.Row([width_input, height_input, quality_input, fmt], wrap=True, spacing=12),
                    ft.Row([keep_aspect, overwrite], wrap=True),
                    ft.FilledButton("Procesar imágenes", icon=ft.Icons.PHOTO_SIZE_SELECT_LARGE, on_click=run),
                    preview,
                ],
            )
        )

    def show_cut_join(self) -> None:
        self.selected = []
        self.status.value = ""
        start_input = ft.TextField(label="Inicio", hint_text="00:00:05", value="0", width=160)
        end_input = ft.TextField(label="Fin (vacío = hasta el final)", hint_text="00:00:20", width=220)
        summary, buttons = self._selection_row("both", [ext.lstrip(".") for ext in VIDEO_EXTS])
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(VIDEO_EXTS, sort=False)
            preview.controls = [self.file_list(files)]
            self.page.update()

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[ext.lstrip(".") for ext in sorted(VIDEO_EXTS)],
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def require_ffmpeg() -> bool:
            if ffmpeg_available():
                return True
            self.notify("Necesitas ffmpeg instalado para cortar o unir video.", error=True)
            return False

        def run_cut(e=None):
            if not require_ffmpeg():
                return
            files = self.gather_files(VIDEO_EXTS, sort=False)
            end_value = (end_input.value or "").strip() or None
            self._run_batch(
                files,
                lambda path: cut_clip(path, start=start_input.value or "0", end=end_value),
                empty="Selecciona videos para cortar.",
                done_label="Videos cortados",
            )

        def run_join(e=None):
            if not require_ffmpeg():
                return
            files = self.gather_files(VIDEO_EXTS, sort=False)
            if len(files) < 2:
                self.notify("Selecciona al menos dos videos para unir.", error=True)
                return
            if self._busy:
                return
            self.set_busy(True, 0, 1)
            try:
                dest = join_clips(files)
                self.notify(f"Video unido: {dest.name}")
                open_path(dest.parent)
            except Exception as err:
                self.notify(f"Error: {err}", error=True)
            finally:
                self.set_busy(False, 1, 1)

        self.set_view(
            self.tool_scaffold(
                "Cortar / unir video",
                "Corta un fragmento (inicio/fin) o une los videos en el orden en que los seleccionaste.",
                [
                    summary,
                    buttons,
                    ft.Row([start_input, end_input], wrap=True, spacing=12),
                    ft.Row(
                        [
                            ft.FilledButton("Cortar", icon=ft.Icons.CONTENT_CUT, on_click=run_cut),
                            ft.OutlinedButton("Unir seleccionados", icon=ft.Icons.MERGE, on_click=run_join),
                        ],
                        wrap=True,
                    ),
                    preview,
                ],
            )
        )

    def show_whatsapp(self) -> None:
        self.selected = []
        self.status.value = ""
        preset = ft.Dropdown(
            label="Calidad",
            value="720p",
            options=[
                ft.DropdownOption(key="720p", text="720p (mejor calidad)"),
                ft.DropdownOption(key="480p", text="480p (más liviano)"),
            ],
            width=260,
        )
        summary, buttons = self._selection_row("both", [ext.lstrip(".") for ext in VIDEO_EXTS])
        preview = ft.Column()

        def refresh(e=None):
            files = self.gather_files(VIDEO_EXTS)
            preview.controls = [self.file_list(files)]
            self.page.update()

        async def pick_files(e=None):
            files = await self.picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[ext.lstrip(".") for ext in sorted(VIDEO_EXTS)],
            )
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path()
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
        ]

        def run(e=None):
            if not ffmpeg_available():
                self.notify("Necesitas ffmpeg instalado para comprimir video.", error=True)
                return
            files = self.gather_files(VIDEO_EXTS)
            self._run_batch(
                files,
                lambda path: compress_for_whatsapp(path, preset=preset.value or "720p"),
                empty="Selecciona videos para comprimir.",
                done_label="Videos listos para WhatsApp",
            )

        self.set_view(
            self.tool_scaffold(
                "Comprimir para WhatsApp",
                "Crea un MP4 H.264 liviano (yuv420p + AAC) sin tocar el original.",
                [
                    summary,
                    buttons,
                    preset,
                    ft.FilledButton("Comprimir", icon=ft.Icons.CHAT, on_click=run),
                    preview,
                ],
            )
        )

    def show_organize(self) -> None:
        self.selected = []
        self.status.value = ""
        layout = ft.Dropdown(
            label="Carpetas",
            value="year_month",
            options=[
                ft.DropdownOption(key="year_month", text="Año / mes  (2024/08)"),
                ft.DropdownOption(key="year_month_day", text="Año / mes / día"),
            ],
            expand=True,
        )
        move = ft.Checkbox(label="Mover (en vez de copiar)", value=False)
        recursive = ft.Checkbox(label="Incluir subcarpetas", value=True)
        dest_label = ft.Text("Carpeta destino: la misma de origen", size=13, color=MUTED, selectable=True)
        dest_folder: list[str] = []
        summary, buttons = self._selection_row("both")
        preview_box = ft.Column()

        def source_root() -> Path | None:
            if not self.selected:
                return None
            path = Path(self.selected[0])
            return path if path.is_dir() else path.parent

        def dest_root() -> Path | None:
            if dest_folder:
                return Path(dest_folder[0])
            return source_root()

        def refresh(e=None):
            preview_box.controls.clear()
            files = self.gather_files(recursive=bool(recursive.value))
            root = dest_root()
            if not files or root is None:
                preview_box.controls.append(ft.Text("Selecciona archivos o una carpeta para ver el destino.", color=MUTED))
                self.page.update()
                return
            try:
                plan = build_organize_plan(files, root, layout=layout.value or "year_month")
                preview_box.controls.append(
                    ft.Text(f"{len(plan)} archivos → {root}", color=CYAN, weight=ft.FontWeight.BOLD)
                )
                for item in plan[:30]:
                    relative = item.destination.relative_to(root)
                    preview_box.controls.append(
                        ft.Text(
                            f"{item.source.name}  →  {relative}  ({item.taken_at:%Y-%m-%d})",
                            size=12,
                            color=ft.Colors.WHITE70,
                        )
                    )
                if len(plan) > 30:
                    preview_box.controls.append(ft.Text(f"… y {len(plan) - 30} más", color=MUTED, size=12))
            except Exception as err:
                preview_box.controls.append(ft.Text(str(err), color=ft.Colors.RED_400))
            self.page.update()

        recursive.on_change = refresh
        layout.on_select = refresh

        async def pick_files(e=None):
            files = await self.picker.pick_files(allow_multiple=True)
            if files:
                self.selected = [f.path for f in files if f.path]
                summary.value = self.selected_label()
                refresh()

        async def pick_folder(e=None):
            path = await self.picker.get_directory_path(dialog_title="Carpeta de origen")
            if path:
                self.selected = [path]
                summary.value = self.selected_label()
                refresh()

        async def pick_dest(e=None):
            path = await self.picker.get_directory_path(dialog_title="Carpeta destino")
            if path:
                dest_folder.clear()
                dest_folder.append(path)
                dest_label.value = f"Carpeta destino: {path}"
                refresh()

        buttons.controls = [
            ft.FilledButton("Archivos", icon=ft.Icons.INSERT_DRIVE_FILE, on_click=pick_files),
            ft.OutlinedButton("Carpeta origen", icon=ft.Icons.FOLDER_OPEN, on_click=pick_folder),
            ft.TextButton("Elegir destino", icon=ft.Icons.DRIVE_FILE_MOVE, on_click=pick_dest),
        ]

        def run(e=None):
            files = self.gather_files(recursive=bool(recursive.value))
            root = dest_root()
            if not files or root is None:
                self.notify("Selecciona archivos y una carpeta destino.", error=True)
                return
            try:
                plan = build_organize_plan(files, root, layout=layout.value or "year_month")
                count = apply_organize_plan(plan, move=bool(move.value))
                self.notify(f"Organizados {count} archivos en {root}")
                open_path(root)
                refresh()
            except Exception as err:
                self.notify(f"Error: {err}", error=True)

        self.set_view(
            self.tool_scaffold(
                "Organizar por fecha",
                "Usa la fecha de la foto (EXIF) si existe; si no, la fecha de modificación del archivo.",
                [
                    summary,
                    buttons,
                    dest_label,
                    ft.Row([layout, move, recursive], wrap=True, spacing=12),
                    ft.Row(
                        [
                            ft.FilledButton("Organizar", icon=ft.Icons.DATE_RANGE, on_click=run),
                            ft.TextButton("Vista previa", on_click=refresh),
                        ],
                        wrap=True,
                    ),
                    ft.Container(bgcolor=CARD_BG, border_radius=12, padding=16, content=preview_box),
                ],
            )
        )
        preview_box.controls.append(ft.Text("Selecciona archivos o una carpeta para ver el destino.", color=MUTED))

    def _run_batch(self, files: list[Path], worker, *, empty: str, done_label: str) -> None:
        if self._busy:
            return
        if not files:
            self.notify(empty, error=True)
            return
        ok = 0
        errors: list[str] = []
        last_dir = files[0].parent
        self.set_busy(True, 0, len(files))
        try:
            for index, path in enumerate(files, start=1):
                try:
                    worker(path)
                    ok += 1
                except Exception as err:
                    errors.append(f"{path.name}: {err}")
                self.set_busy(True, index, len(files))
        finally:
            self.set_busy(False, len(files), len(files))
        if errors and ok:
            self.notify(f"{done_label}: {ok}. Fallaron {len(errors)}. {errors[0]}")
        elif errors:
            self.notify(f"Error: {errors[0]}", error=True)
        else:
            self.notify(f"{done_label}: {ok} archivo(s).")
            open_path(last_dir)


def main(page: ft.Page):
    MediaToolboxApp(page)


if __name__ == "__main__":
    ft.app(target=main)
