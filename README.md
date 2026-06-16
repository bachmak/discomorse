# Morse Decoder

Real-time Morse code decoder. Browser captures or uploads audio; a Python backend detects the carrier, decodes timing, and streams corrected text back over WebSocket. A waterfall and FFT spectrum are rendered live in the browser.

---

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 22+
- FFmpeg (required by pydub for audio file decoding)
- Docker + Docker Compose (for containerised deployment)

---

## Local development

**Backend**

```bash
cd backend
uv sync
uv run uvicorn morse_decoder.api.routes:app --reload
```

The API is available at `http://localhost:8000`. Copy `config.toml` to `config.local.toml` for local overrides — it is gitignored.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The dev server is available at `http://localhost:5173` with hot reload.

---

## Docker

```bash
docker compose up --build
```

Starts backend, frontend (nginx), and Caddy reverse proxy. The app is served at `http://localhost`.

---

## Code quality

```bash
# Backend
uv run ruff check src
uv run mypy --strict src

# Frontend
npm run lint
npm run typecheck
```

Pre-commit hooks run ruff and mypy automatically. Install them once with:

```bash
pip install pre-commit && pre-commit install
```
