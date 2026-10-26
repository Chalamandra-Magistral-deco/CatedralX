# CatedralX v1.0-canónico - Release Image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CATEDRALX_SNAPSHOT_PATH=/dev/shm/cathedral_snapshot.json \
    PATH="/app/BIN:${PATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash catedralx

COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir numpy pytest; fi

COPY elite/ ./elite/
COPY BIN/ ./BIN/

RUN chmod +x BIN/catedral && chown -R catedralx:catedralx /app

USER catedralx

# Healthcheck y comando por defecto
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD catedral status || exit 1
CMD ["catedral", "status"]
