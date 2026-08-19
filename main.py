"""Punto de entrada de Media Toolbox."""

import os
from pathlib import Path

import flet as ft

from app import main


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def run() -> None:
    web = _env_flag("FLET_FORCE_WEB_SERVER")
    port = int(os.getenv("FLET_SERVER_PORT", "8080" if web else "0"))
    host = os.getenv("FLET_SERVER_IP") or ("0.0.0.0" if web else None)
    upload = os.getenv("MEDIA_TOOLBOX_UPLOAD_DIR")
    if upload:
        Path(upload).mkdir(parents=True, exist_ok=True)
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER if web else ft.AppView.FLET_APP,
        host=host,
        port=port,
        upload_dir=upload,
    )


if __name__ == "__main__":
    run()
