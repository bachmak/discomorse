FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml config.toml ./
COPY src/ src/

RUN uv pip install --system -e .

CMD ["uvicorn", "morse_decoder.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
