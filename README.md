# Media Toolbox

Caja de herramientas de escritorio (Flet) para organizar y procesar fotos, audio y video.

## Qué incluye (v2.1)

- **Renombrar archivos** por lote, con vista previa, numeración, patrones y deshacer.
- **Borrar toda la metadata** (EXIF, GPS, etiquetas, capítulos y metadatos de contenedor).
- **Cortar / unir video** por tiempo o en el orden de selección.
- **Comprimir para WhatsApp** (MP4 720p o 480p).
- **Organizar por fecha** en carpetas `Año/Mes` (usa EXIF si existe).
- **Extraer audio** de un video (MP3, WAV, M4A, OGG, FLAC).
- **Convertir** video y audio a otro formato.
- **Imágenes**: redimensionar, comprimir y convertir JPG/PNG/WebP/BMP.

Las herramientas de audio y video necesitan [ffmpeg](https://ffmpeg.org/download.html) en el PATH.

## Cómo ejecutarlo

```bash
python -m pip install -r requirements.txt
python main.py
```

En Linux, el selector de archivos de Flet también necesita Zenity:

```bash
sudo apt-get install zenity ffmpeg
```

## Empaquetar (Windows)

```bash
pyinstaller main.spec
```
