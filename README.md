# Media Toolbox

Caja de herramientas de escritorio (Flet) para organizar y procesar fotos, audio y video.

## Qué incluye (v2.2)

- **Renombrar archivos** por lote, con vista previa, numeración, patrones y deshacer.
- **Borrar toda la metadata** (EXIF, GPS, etiquetas, capítulos y metadatos de contenedor).
- **Cortar / unir video** con vista previa de fotogramas de inicio y fin.
- **Girar / voltear video** (90°, 180°, horizontal y vertical).
- **HEIC a JPG** para fotos de iPhone.
- **Comprimir para WhatsApp** (MP4 720p o 480p).
- **Organizar por fecha** en carpetas `Año/Mes` (usa EXIF si existe).
- **Extraer audio**, convertir formatos y redimensionar imágenes.

Las herramientas de audio y video necesitan [ffmpeg](https://ffmpeg.org/download.html) en el PATH. HEIC necesita `pillow-heif`.

## Instalar desde GitHub

Como aplicación (recomendado):

```bash
python -m pip install "git+https://github.com/Jalvala147/media-toolbox.git"
media-toolbox
```

O clonar y correr en desarrollo:

```bash
python -m pip install -r requirements.txt
python main.py
```

En Linux, el selector de archivos de Flet también necesita Zenity:

```bash
sudo apt-get install zenity ffmpeg
```

## Publicar un package / release

Cada tag `vX.Y.Z` dispara GitHub Actions y publica:

1. Un **GitHub Release** con el wheel de Python y (en Windows) `MediaToolbox.exe`
2. El paquete pip en **GitHub Packages**

```bash
git tag v2.2.0
git push origin v2.2.0
```

El resultado queda en [Releases](https://github.com/Jalvala147/media-toolbox/releases) y en [Packages](https://github.com/Jalvala147/media-toolbox/packages).

Para instalar el package de GitHub Packages (pide autenticación):

```bash
python -m pip install media-toolbox --index-url https://pypi.pkg.github.com/Jalvala147/simple/
```

## Empaquetar en tu PC (Windows)

```bash
pyinstaller main.spec
```

El ejecutable sale en `dist/MediaToolbox.exe`.
