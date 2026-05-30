"""In-memory audio synthesis for tests.

No binary fixtures are committed: each test builds a known signal (a pure
tone) and encodes it as WAV bytes — the input shape ``FileSource`` accepts.
WAV keeps decoding deterministic.
"""

import io

import numpy as np
import numpy.typing as npt
import soundfile as sf  # type: ignore[import-untyped]  # no stubs

_INT16_MAX = 32767


def sine_pcm(
    freq_hz: float, duration_s: float, sample_rate: int
) -> npt.NDArray[np.int16]:
    """Mono Int16 samples of a half-amplitude pure tone."""
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    return (0.5 * np.sin(2 * np.pi * freq_hz * t) * _INT16_MAX).astype(np.int16)


def wav_bytes(
    samples: npt.NDArray[np.int16], sample_rate: int, channels: int = 1
) -> bytes:
    """Encode mono Int16 samples as WAV, duplicated across ``channels``."""
    frames = samples if channels == 1 else np.tile(samples[:, None], (1, channels))
    buffer = io.BytesIO()
    sf.write(buffer, frames, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def sine_wav(
    freq_hz: float, duration_s: float, sample_rate: int, channels: int = 1
) -> bytes:
    """WAV bytes of a pure tone — ``sine_pcm`` composed with ``wav_bytes``."""
    return wav_bytes(sine_pcm(freq_hz, duration_s, sample_rate), sample_rate, channels)
