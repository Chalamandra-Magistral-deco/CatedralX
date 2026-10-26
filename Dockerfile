FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CATEDRALX_SNAPSHOT_PATH=/dev/shm/cathedral_snapshot.json \
    PATH="/app/BIN:${PATH}"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash catedralx
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir numpy pytest psutil; fi
COPY elite/ ./elite/
COPY BIN/ ./BIN/
RUN chmod +x BIN/catedral && chown -R catedralx:catedralx /app
USER catedralx
# CLI de ejecución puntual: status finaliza el proceso; no aplica HEALTHCHECK de servicio.
CMD ["catedral","status"]
