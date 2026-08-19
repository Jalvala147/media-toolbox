FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/Jalvala147/media-toolbox"
LABEL org.opencontainers.image.title="Media Toolbox"
LABEL org.opencontainers.image.description="Caja de herramientas para foto, audio y video"
LABEL org.opencontainers.image.version="2.2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libheif1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md main.py app.py index.py ./
COPY core ./core

RUN pip install --no-cache-dir .

ENTRYPOINT ["media-toolbox"]
