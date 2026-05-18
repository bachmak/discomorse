# Architecture Decision Record — Intelligent Morse Code Decoder

## Overview

Web-based, real-time Morse code decoder. Python backend handles all signal processing and decoding; React frontend handles visualization and user interaction. Communication via WebSockets.

---

## Stack Summary

| Concern | Decision |
|---|---|
| Frontend | React + TypeScript + Vite |
| Frontend state | Zustand |
| Backend | FastAPI (Python 3.12) |
| Package manager | uv |
| Interprocess communication | asyncio.Queue between pipeline stages |
| Signal processing | numpy + scipy |
| Audio file decoding | pydub + FFmpeg (system dependency) |
| Server-side audio capture | sounddevice (optional plugin) |
| Config | config.toml + pydantic-settings (env var overrides) |
| Code quality | ruff + pre-commit + mypy --strict |
| Containerization | docker-compose (backend + frontend + Caddy) |
| Reverse proxy | Caddy (automatic HTTPS via Let's Encrypt) |
| Repository | Monorepo on GitLab |
| Branching | GitHub Flow (short-lived feature branches → main via MR) |
| CI/CD | GitLab CI: lint, typecheck, build, Docker build, security scan |

---

## Repository Structure

```
morse-decoder/
├── backend/
│   ├── src/
│   │   └── morse_decoder/
│   │       ├── api/          # FastAPI routes, WebSocket handlers
│   │       ├── audio/        # AudioSource plugins
│   │       ├── pipeline/     # Stage 1, 1.5, 2 + queue wiring
│   │       ├── plugins/      # Plugin interfaces + factory
│   │       └── config.py     # pydantic-settings model
│   ├── config.toml           # Default settings, committed to repo
│   ├── config.local.toml     # Local overrides, gitignored
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Waterfall, FFTSpectrum, DecodedText
│   │   ├── hooks/            # useWebSocket, useAudioCapture
│   │   └── types/            # Shared TypeScript types
│   ├── package.json
│   └── Dockerfile
├── models/                   # Language model corpus files (per language)
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── Caddyfile
├── .gitlab-ci.yml
└── .pre-commit-config.yaml
```

---

## Audio Input

Three `AudioSource` plugin implementations sharing a common interface:

| Plugin | Description |
|---|---|
| `BrowserMicSource` | Web Audio API in the browser; streams 8 kHz Int16 PCM over WebSocket |
| `FileSource` | REST file upload (mp3/wav); decoded via pydub + FFmpeg |
| `ServerDeviceSource` | Server-side sounddevice capture; for WebSDR via virtual audio cable (optional) |

**Audio format over WebSocket:**
- Sample rate: 8 kHz (downsampled in browser via `OfflineAudioContext`)
- Encoding: Int16 PCM
- Chunk size: 2048 samples (~256 ms per chunk)
- Latency budget: < 500 ms end-to-end

---

## Signal Processing — Tone Detection

**Algorithm: STFT (Short-Time Fourier Transform) with continuous carrier tracking.**

- Computes spectrogram continuously over overlapping windows
- Tracks the dominant frequency peak across frames to lock onto the CW carrier
- Carrier frequency is unknown at startup and may drift over time — continuous peak tracking handles both
- STFT output feeds the waterfall visualization at zero extra cost
- Robustness is prioritized over speed; latency budget is relaxed (< 500 ms)

The `ToneDetector` is a plugin. Alternative implementations (Goertzel, ML-based) can replace the default via config.

---

## Decoding Pipeline

Three sequential stages connected by `asyncio.Queue` pairs:

```
AudioSource
    │  raw PCM chunks
    ▼
[Stage 1] TimingDecoder
    │  sequence of: Dit | Dah | IntraCharSpace | InterCharSpace | WordSpace
    ▼
[Stage 1.5] LetterDecoder
    │  stream of typed tokens: Letter | Digit | Prosign | Unknown
    ▼
[Stage 2] Interpreter
    │  corrected, readable text
    ▼
WebSocket → Frontend
```

### Stage 1 — Timing Decoder

**Algorithm: adaptive thresholding.**

Maintains a running estimate of the current dit duration, updated from recent elements. Classifies all ON/OFF durations as ratios of that estimate:
- Dah ≈ 3× dit
- Inter-character space ≈ 3× dit
- Word space ≈ 7× dit

Handles variable WPM automatically. Replaceable via plugin interface.

### Stage 1.5 — Letter Decoder

**Algorithm: ITU Morse code dictionary lookup.**

Pure deterministic function. Maps dit/dah sequences (e.g. `".-"` → `A`) using the full ITU table including digits, punctuation, and prosigns. Outputs typed tokens so Stage 2 knows whether it is handling a letter, digit, prosign, or an unrecognized sequence.

Fully unit-testable in isolation. No ML, no state.

### Stage 2 — Interpreter

**TODO: choose between two plugin implementations.**

Both implement the same `Interpreter` interface. No external API calls.

| Option | Description |
|---|---|
| Noisy channel model | `P(correct \| observed) ∝ P(observed \| correct) × P(correct)`. Error model tuned to Morse-specific confusions; language model is an N-gram trained on QSO corpus. Offline, fast, domain-aware. Multi-language = swap corpus. |
| Local pre-trained model | Small HuggingFace seq2seq model (e.g. grammar correction variant) used directly without additional fine-tuning. Better general English correction; weaker on QSO-specific abbreviations. |

Decision deferred. Architecture accommodates either — both register under the same `Interpreter` plugin interface.

---

## Plugin Architecture

Each swappable component has a base class (abstract, fully typed). A `PluginFactory` reads `config.toml` and instantiates the configured implementation from a registry dict. Fully type-safe and mypy-verifiable.

```toml
# config.toml
[pipeline]
tone_detector = "STFTDetector"
timing_decoder = "AdaptiveThresholdDecoder"
interpreter = "NoisyChannelInterpreter"
language = "en"
```

Adding a new language: add a corpus/model file under `models/<lang>/`, register the language code in config. No code changes required.

---

## Visualization

Both rendered via HTML5 Canvas in the browser, updated from WebSocket frames:

| Panel | Description |
|---|---|
| Waterfall (spectrogram) | Scrolling time-frequency display. Data comes directly from the STFT already computed by Stage 1 — zero extra computation. Primary view for monitoring the CW carrier and signal quality. |
| FFT Spectrum | Current-frame frequency content. Shows instantaneous power across the spectrum. Secondary panel. |

---

## Frontend Architecture

- **React + TypeScript + Vite** — component framework and build tool
- **Zustand** — global store for WebSocket data (waterfall frames, FFT frames, decoded text). High-frequency visualization updates do not trigger re-renders in unrelated components.
- **PWA-ready** — Vite PWA plugin for installable mobile support
- **Web Audio API** — browser-side mic capture and downsampling (`OfflineAudioContext`)

---

## Configuration

Two-layer config via pydantic-settings:

1. **`config.toml`** — application defaults (pipeline parameters, plugin selection, FFT window size, sample rate, etc.). Committed to the repository.
2. **Environment variables** — deployment overrides (host, port, secrets). Set in `docker-compose.yml` or server environment. Never committed.

`config.local.toml` for local developer overrides, gitignored.

---

## Typing

Strict typing enforced throughout the Python backend:
- `mypy --strict` in CI — no exceptions
- Pydantic v2 models for all inter-stage data transfer objects, WebSocket message schemas, plugin configs, and app settings
- All FastAPI request/response bodies are Pydantic models
- TypeScript strict mode on the frontend

---

## CI/CD (GitLab)

Path-based triggers: backend jobs only run when `backend/` changes; frontend jobs only when `frontend/` changes.

| Stage | Jobs |
|---|---|
| Lint | ruff (Python), ESLint (TypeScript) |
| Typecheck | mypy --strict (Python), tsc (TypeScript) |
| Build | React production build verification |
| Docker | Build backend + frontend images |
| Security | pip audit, npm audit |

Pre-commit hooks run ruff + mypy locally before each commit.

---

## Deployment

| Environment | Setup |
|---|---|
| Local development | Vite dev server (port 5173) + FastAPI (port 8000), CORS configured for localhost. No proxy. |
| Self-hosted server | docker-compose with three services: backend, frontend (nginx serving static build), Caddy (reverse proxy + automatic HTTPS via Let's Encrypt) |

---

## Open Decisions

- **Stage 2 Interpreter implementation:** noisy channel model vs. local pre-trained HuggingFace model. To be decided during implementation.
