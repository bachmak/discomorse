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

Decode an audio file offline to inspect what the pipeline makes of it:

```bash
cd backend
uv run python scripts/decode_file.py test_audio/<audio-file-name>
```

The interpreter groups letters into words against a word list shipped under
`src/morse_decoder/models/<language>/`. It is committed, so nothing needs
rebuilding to run the app. To regenerate it, or to add a language:

```bash
cd backend
curl -L -o count_1w.txt https://norvig.com/ngrams/count_1w.txt
uv run python scripts/build_lexicon.py count_1w.txt --language en
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The dev server is available at `http://localhost:5173` with hot reload. It proxies
`/api` and `/ws` to the backend on `http://localhost:8000`, the same prefixes Caddy
serves in Docker, so start the backend first.

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
uv run ruff check src scripts
uv run mypy --strict src scripts
uv run pytest tests
uv run python scripts/smoke_pipeline.py  # end-to-end pipeline smoke test

# Frontend
npm run lint
npm run typecheck
```

Pre-commit hooks run ruff and mypy automatically. Install them once with:

```bash
pip install pre-commit && pre-commit install
```
