# Media Toolbox

Caja de herramientas de escritorio (Flet) para organizar y procesar fotos, audio y video.

## Qué incluye (v2.0)

- **Renombrar archivos** por lote, con vista previa, numeración, patrones y deshacer.
- **Limpiar metadatos** (EXIF de imágenes y etiquetas de audio/video).
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
