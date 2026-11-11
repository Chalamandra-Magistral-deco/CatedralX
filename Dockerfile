FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CATEDRALX_SNAPSHOT_PATH=/dev/shm/cathedral_snapshot.json \
    PATH="/app/BIN:${PATH}"
WORKDIR /app
RUN useradd --create-home --shell /bin/bash catedralx
COPY requirements-runtime.lock ./
RUN python -m pip install --no-cache-dir --requirement requirements-runtime.lock \
    && python -m pip check
COPY elite/ ./elite/
COPY BIN/ ./BIN/
RUN chmod +x BIN/catedral \
    && mkdir -p /home/catedralx/.local/state/chalamandra/catedralx \
    && chown -R catedralx:catedralx /app /home/catedralx
USER catedralx
# One-shot CLI: status exits; this image is not a long-running HTTP service.
CMD ["catedral", "status"]
