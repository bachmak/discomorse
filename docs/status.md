# Project Status

## Backend

| File | State |
|---|---|
| `pyproject.toml` | Done — uv, all deps, ruff + mypy config |
| `config.toml` | Done — default values for all sections |
| `config.local.toml` | Gitignored, not created — add locally as needed |
| `Dockerfile` | Done — uv install (no FFmpeg; soundfile bundles libsndfile) |
| `src/morse_decoder/config.py` | Done — pydantic-settings, two-layer TOML + env var overrides |
| `src/morse_decoder/audio/base.py` | Done — `AudioSource` ABC |
| `src/morse_decoder/audio/browser_mic.py` | Done — `BrowserMicSource` (asyncio.Queue, push from WS; `EndOfStream` sentinel pushed to end stream) |
| `src/morse_decoder/audio/decoded.py` | Done — `DecodedAudio` DTO (float32 samples + native rate) |
| `src/morse_decoder/audio/decoder.py` | Done — `AudioDecoder` ABC + `SoundFileDecoder` (libsndfile via soundfile) |
| `src/morse_decoder/audio/pcm_normalizer.py` | Done — `PcmNormalizer` (numpy/scipy mono + resample_poly + Int16) |
| `src/morse_decoder/audio/file_source.py` | Done — `FileSource` (soundfile decode → PcmNormalizer → chunked PCM; injectable decoder) |
| `src/morse_decoder/plugins/base.py` | Done — `ToneDetector`, `TimingDecoder`, `Interpreter` ABCs |
| `src/morse_decoder/plugins/factory.py` | Done — decorator registry + `create_*` factory functions |
| `src/morse_decoder/pipeline/types.py` | Done — `MorseElement`, `TokenKind`, `Token` domain DTOs |
| `src/morse_decoder/pipeline/events.py` | Done — `OutboundEvent` hierarchy (Template Method `to_payload`): `MagnitudeFrame` → `WaterfallFrame`/`FFTFrame`, `DecodedText` |
| `src/morse_decoder/pipeline/letter_decoder.py` | Done — full ITU table, pure `decode_sequence` function |
| `src/morse_decoder/pipeline/runner.py` | Done — `PipelineRunner` streams source → detector → decoder → interpreter, yields `OutboundEvent`s (async generator) |
| `src/morse_decoder/api/routes.py` | Stub — `/health` done; `/upload` stub (no pipeline wired yet) |
| `src/morse_decoder/api/websocket.py` | Done — `handle_mic_stream` runs duplex pumps under `TaskGroup`; `BrowserMicSource` ↔ `PipelineRunner` |
| **`STFTDetector`** | **Not implemented** — `ToneDetector` plugin, register with `@register_tone_detector("STFTDetector")` |
| **`AdaptiveThresholdDecoder`** | **Not implemented** — `TimingDecoder` plugin, register with `@register_timing_decoder("AdaptiveThresholdDecoder")` |
| **`NoisyChannelInterpreter`** (or HuggingFace) | **Not implemented** — `Interpreter` plugin, decision still open (see architecture.md) |
| Tests | In progress — pytest wired (`asyncio_mode=auto`); `test_smoke`, `test_file_source` (decode/resample/chunk) |

## Frontend

| File | State |
|---|---|
| `package.json` | Done — React 18, Vite, Zustand, PWA plugin, ESLint, TypeScript |
| `src/types/ws.ts` | Done — discriminated union for all WebSocket message shapes |
| `src/store.ts` | Done — Zustand store (waterfall ring buffer, FFT frame, decoded text) |
| `src/hooks/useWebSocket.ts` | Done — connects to WS, dispatches to store |
| `src/hooks/useAudioCapture.ts` | Done — mic → Int16 PCM via ScriptProcessor |
| `src/components/Waterfall.tsx` | Done — Canvas waterfall renderer |
| `src/components/FFTSpectrum.tsx` | Done — Canvas FFT bar renderer |
| `src/components/DecodedText.tsx` | Done — decoded text display with clear button |
| **`vite.config.ts`** | **Not created** |
| **`tsconfig.json`** | **Not created** |
| **`index.html`** | **Not created** |
| **`src/main.tsx`** | **Not created** |
| **`src/App.tsx`** | **Not created** |
| Tests | **Not started** |
| `Dockerfile` | Done — multi-stage (Vite build → nginx) |

## Infrastructure

| File | State |
|---|---|
| `docker-compose.yml` | Done — backend + frontend + Caddy |
| `Caddyfile` | Done — reverse proxy routes (`/api/*`, `/ws/*` → backend, rest → frontend) |
| `.github/workflows/ci.yml` | Done — path-triggered jobs: lint, typecheck, build, Docker, security |
| `.pre-commit-config.yaml` | Done — ruff + mypy hooks |
| `.gitignore` | Done |
| `models/en/` | Directory created, no corpus files yet |

## What to build next

1. `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/App.tsx` — frontend is not runnable without these
2. `STFTDetector` — core signal processing, unblocks end-to-end testing
3. `AdaptiveThresholdDecoder` — timing stage
4. Wire `/upload` route in `api/routes.py` through the pipeline
5. Decide on and implement `Interpreter` (see open decision in `architecture.md`)
6. Tests — unit tests for `letter_decoder` and `TimingDecoder` are straightforward starting points
