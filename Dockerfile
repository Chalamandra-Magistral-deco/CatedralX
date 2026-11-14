# Imagen base pinneada por digest (python:3.12-slim, 2026-11-14).
# Para subirla: consultar el digest en
# https://hub.docker.com/v2/repositories/library/python/tags/3.12-slim
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ARG CATEDRALX_REVISION=unknown
ARG CATEDRALX_CODE_DIRTY=unknown
LABEL com.chalamandra.catedralx.revision=$CATEDRALX_REVISION
LABEL com.chalamandra.catedralx.code.dirty=$CATEDRALX_CODE_DIRTY
LABEL org.opencontainers.image.revision=$CATEDRALX_REVISION
LABEL org.opencontainers.image.title=Chalamandra-CatedralX
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
