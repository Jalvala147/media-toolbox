# Media Toolbox

Caja de herramientas de escritorio (Flet) para organizar y procesar fotos, audio y video.

## Qué incluye (v2.3)

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

Como paquete de Python:

```bash
python -m pip install "git+https://github.com/Jalvala147/media-toolbox.git"
media-toolbox
```

Los instaladores y wheels también salen en [Releases](https://github.com/Jalvala147/media-toolbox/releases).

O clonar y correr en desarrollo:

```bash
python -m pip install -r requirements.txt
python main.py
```

En Linux, el selector de archivos de Flet también necesita Zenity:

```bash
sudo apt-get install zenity ffmpeg
```

## Docker: interfaz web (sin noVNC)

La imagen de Linux no puede abrir una ventana de escritorio en Windows. Flet sirve la misma app en el navegador, sin escritorio remoto ni noVNC:

```bash
docker pull ghcr.io/jalvala147/media-toolbox:latest
docker run --rm -p 8080:8080 ghcr.io/jalvala147/media-toolbox:latest
```

Abre [http://localhost:8080](http://localhost:8080).

- Elige **archivos** (el navegador no puede ver carpetas del disco de Windows).
- Cuando termina, descarga el resultado (un archivo o un ZIP).
- ffmpeg ya viene en la imagen.
- Para videos muy grandes el `.exe` de Windows suele ir mejor, porque no carga el archivo entero en el navegador.

En desarrollo local también puedes forzar el modo web:

```bash
python -m pip install -e ".[web]"
FLET_FORCE_WEB_SERVER=true FLET_SERVER_IP=0.0.0.0 FLET_SERVER_PORT=8080 python main.py
```

El recuadro **Packages** del repo es esa misma imagen:

```bash
docker pull ghcr.io/jalvala147/media-toolbox:latest
```

## Publicar un package / release

Cada tag `vX.Y.Z` dispara GitHub Actions y crea un **GitHub Release** con:

- el wheel / sdist de Python (`pip install ...`)
- `MediaToolbox.exe` (build de Windows)

```bash
git tag v2.3.0
git push origin v2.3.0
```

El push a `main` también publica `ghcr.io/jalvala147/media-toolbox:latest`.

## Empaquetar en Windows

```bash
pyinstaller main.spec
```

El ejecutable sale en `dist/MediaToolbox.exe`.
