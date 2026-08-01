FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# compile python to bytecode once at image building, not at each container start
ENV UV_COMPILE_BYTECODE=1

# build only dependencies in a separate cached layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# build our project on top of the dependency layer for faster rebuilds
COPY config.toml ./
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

# librosa's numba kernels insist on a writable cache dir
ENV NUMBA_CACHE_DIR=/app/.numba-cache

# change user to avoid running as root
RUN useradd -r app-user && install -d -o app-user $NUMBA_CACHE_DIR
USER app-user

# to immediately see the logs instead of buffering
ENV PYTHONUNBUFFERED=1
# to call python directly instead of through uv
ENV PATH=/app/.venv/bin:$PATH

# define a healthcheck for docker compose
HEALTHCHECK --start-period=10s CMD [ \
    "python", "-m", \
    "morse_decoder.healthcheck" \
]

# run the app
CMD [ \
    "python", "-m", \
    "morse_decoder" \
]
