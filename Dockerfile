FROM python:3.12-slim
ARG CATEDRALX_REVISION=unknown
ARG CATEDRALX_CODE_DIRTY=unknown
LABEL com.chalamandra.catedralx.revision=$CATEDRALX_REVISION
LABEL com.chalamandra.catedralx.code.dirty=$CATEDRALX_CODE_DIRTY
LABEL org.opencontainers.image.revision=$CATEDRALX_REVISION
LABEL org.opencontainers.image.title=Chalamandra-CatedralX
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
