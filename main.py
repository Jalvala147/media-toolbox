# main.py

import os
import flet as ft
from core.rename import rename_files
from core.zip_files import rename_and_zip

IS_WEB = False  # <<--- AQUÍ defines si vas a correr en WEB o ESCRITORIO

def main(page: ft.Page):
    page.title = "Renombrador de Archivos"
    page.bgcolor = ft.colors.GREY_100
    page.scroll = ft.ScrollMode.AUTO
    page.window_width = 600
    page.window_height = 550

    uploaded_files = []

    folder_input = ft.TextField(label="Ruta de la carpeta", expand=True, read_only=True)
    name_input = ft.TextField(label="Nuevo nombre base", expand=True)
    ext_input = ft.TextField(label="Filtrar por extensión (opcional, ej: .jpg)", expand=True)
    result_text = ft.Text("", size=16)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def seleccionar_carpeta(e):
        if IS_WEB:
            file_picker.pick_files(allow_multiple=True)
        else:
            file_picker.get_directory_path()

    def folder_selected(e: ft.FilePickerResultEvent):
        if IS_WEB:
            uploaded_files.clear()
            if e.files:
                for f in e.files:
                    uploaded_files.append({
                        "name": f.name,
                        "content": f.bytes_data
                    })
                folder_input.value = f"{len(uploaded_files)} archivos seleccionados"
        else:
            if e.path:
                folder_input.value = e.path
        page.update()

    file_picker.on_result = folder_selected

    def renombrar_click(e):
        folder = folder_input.value.strip()
        new_name = name_input.value.strip()
        extension = ext_input.value.strip()

        if not new_name or (not folder and not uploaded_files):
            result_text.value = "⚠️ Debes seleccionar carpeta o archivos, y escribir nombre nuevo."
            result_text.color = ft.colors.RED_400
            page.update()
            return

        try:
            if IS_WEB:
                if not uploaded_files:
                    raise Exception("No se subieron archivos.")
                zip_data = rename_and_zip(uploaded_files, new_name, extension if extension else None)
                page.launch_file(zip_data, name="renombrados.zip")
                result_text.value = f"✅ Archivos renombrados y descargados."
                result_text.color = ft.colors.GREEN_600
            else:
                count = rename_files(folder, new_name, extension if extension else None)
                result_text.value = f"✅ Renombrados {count} archivos."
                result_text.color = ft.colors.GREEN_600
        except Exception as err:
            result_text.value = f"❌ Error: {str(err)}"
            result_text.color = ft.colors.RED_400

        page.update()

    folder_button = ft.FilledButton("Seleccionar carpeta o archivos", on_click=seleccionar_carpeta, icon=ft.icons.FOLDER_OPEN)
    rename_button = ft.FilledButton("Renombrar archivos", on_click=renombrar_click, icon=ft.icons.DRIVE_FILE_RENAME_OUTLINE)

    form = ft.Column(
        [
            folder_input,
            folder_button,
            name_input,
            ext_input,
            rename_button,
            result_text
        ],
        spacing=20,
        tight=True,
    )

    page.add(
        ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=form,
                    padding=30,
                )
            ),
            alignment=ft.alignment.center,
            padding=30,
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.FLET_APP)  
