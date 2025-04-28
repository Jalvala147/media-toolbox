import flet as ft

def main(page: ft.Page):
    page.title = "Media Toolbox"
    page.bgcolor = ft.colors.BLACK
    page.window_width = 600
    page.window_height = 600
    page.scroll = ft.ScrollMode.HIDDEN
    page.theme_mode = ft.ThemeMode.DARK

    # Animación al cambiar de vistas
    def cambiar_vista(view_func):
        page.clean()
        page.add(view_func())

    # --- Vistas (pantallas) ---

    def home_view():
        return ft.Column(
            [
                ft.Text(
                    "🎛️ Media Toolbox",
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    text_align="center",
                    color=ft.colors.CYAN_400,
                ),
                ft.Divider(height=30, color=ft.colors.CYAN_400),
                ft.FilledButton("📁 Renombrar archivos", on_click=lambda e: cambiar_vista(renombrar_view), style=boton_style()),
                ft.FilledButton("🧹 Limpiar metadatos", on_click=lambda e: cambiar_vista(limpiar_view), style=boton_style()),
                ft.FilledButton("🎬 Extraer audio de video", on_click=lambda e: cambiar_vista(extraer_audio_view), style=boton_style()),
                ft.Divider(height=40, color=ft.colors.CYAN_400),
                ft.Text(
                    "Versión 1.0 - by Jalvala",
                    size=12,
                    color=ft.colors.with_opacity(0.5, ft.colors.WHITE),
                    text_align="center"
                )
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def renombrar_view():
        return pantalla_basica("🔤 Renombrar archivos", "Renamer...")

    def convertir_view():
        return pantalla_basica("🎵 Convertir MP4 a MP3", "Converter...")

    def limpiar_view():
        return pantalla_basica("🧹 Limpiar metadatos", "Metadata eraser...")

    def extraer_audio_view():
        return pantalla_basica("🎬 Extraer audio", "Extracter...")

    def pantalla_basica(titulo, contenido):
        return ft.Column(
            [
                ft.Text(titulo, size=30, weight=ft.FontWeight.BOLD, color=ft.colors.CYAN_400),
                ft.Text(contenido, size=16, text_align="center", color=ft.colors.WHITE),
                ft.Divider(height=30),
                ft.FilledButton("🏠 Volver al inicio", on_click=lambda e: cambiar_vista(home_view), style=boton_style())
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def boton_style():
        return ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=20,
            bgcolor=ft.colors.with_opacity(0.8, ft.colors.CYAN_800),
            color=ft.colors.WHITE,
            overlay_color=ft.colors.CYAN_200,
        )

    # --- Inicializar ---
    page.add(home_view())

if __name__ == "__main__":
    ft.app(target=main)
