"""In-memory audio synthesis and clocks for tests.

No binary fixtures are committed: each test builds a known signal (a pure
tone) and encodes it as WAV bytes — the input shape ``FileSource`` accepts.
WAV keeps decoding deterministic.
"""

import datetime
import io

import numpy as np
import numpy.typing as npt
import soundfile as sf  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.audio.pcm16 import PCM16

EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)


def sine_pcm(
    freq_hz: float, duration_s: float, sample_rate: int
) -> npt.NDArray[PCM16.IntType]:
    """Mono Int16 samples of a half-amplitude pure tone."""
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    return (0.5 * np.sin(2 * np.pi * freq_hz * t) * PCM16.INT_PEAK).astype(
        PCM16.IntType
    )


def wav_bytes(
    samples: npt.NDArray[PCM16.IntType], sample_rate: int, channels: int = 1
) -> bytes:
    """Encode mono Int16 samples as WAV, duplicated across ``channels``."""
    frames = samples if channels == 1 else np.tile(samples[:, None], (1, channels))
    buffer = io.BytesIO()
    sf.write(buffer, frames, sample_rate, format="WAV", subtype=PCM16.WavSubtype)
    return buffer.getvalue()


def sine_wav(
    freq_hz: float, duration_s: float, sample_rate: int, channels: int = 1
) -> bytes:
    """WAV bytes of a pure tone — ``sine_pcm`` composed with ``wav_bytes``."""
    return wav_bytes(sine_pcm(freq_hz, duration_s, sample_rate), sample_rate, channels)


def epoch_clock(sample_rate: int) -> SampleClock:
    """A clock anchored at the epoch, so stamps are absolute and reproducible."""
    return SampleClock(sample_rate=sample_rate, started_at=EPOCH)
