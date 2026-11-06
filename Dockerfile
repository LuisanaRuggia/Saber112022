FROM ghcr.io/astral-sh/uv:0.5.31 AS uv

FROM python:3.12-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY saber11 ./saber11
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 saber11 \
    && mkdir -p /app/output /data \
    && chown -R saber11:saber11 /app /data
WORKDIR /app
COPY --from=build --chown=saber11:saber11 /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    SABER11_OUTPUT_DIR=/app/output
USER saber11
VOLUME ["/app/output", "/data"]
HEALTHCHECK CMD python -c "import saber11"
ENTRYPOINT ["python", "-m", "saber11"]
CMD ["run"]
