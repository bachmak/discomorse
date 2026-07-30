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
    freq_hz: float, duration_s: float, sample_rate: int, amplitude: float = 0.5
) -> npt.NDArray[PCM16.IntType]:
    """Mono Int16 samples of a pure tone; ``amplitude`` 1.0 is full scale."""
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    return (amplitude * np.sin(2 * np.pi * freq_hz * t) * PCM16.INT_PEAK).astype(
        PCM16.IntType
    )


def chirp_pcm(
    start_hz: float,
    end_hz: float,
    duration_s: float,
    sample_rate: int,
    amplitude: float = 0.5,
) -> npt.NDArray[PCM16.IntType]:
    """Mono Int16 samples of a tone sweeping linearly ``start_hz`` -> ``end_hz``."""
    t = np.arange(int(sample_rate * duration_s)) / sample_rate
    sweep_hz_per_s = (end_hz - start_hz) / duration_s
    phase = 2 * np.pi * (start_hz * t + sweep_hz_per_s * t * t / 2)
    return (amplitude * np.sin(phase) * PCM16.INT_PEAK).astype(PCM16.IntType)


def noise_pcm(
    duration_s: float, sample_rate: int, amplitude: float = 0.05, seed: int = 0
) -> npt.NDArray[PCM16.IntType]:
    """Mono Int16 samples of white noise; ``amplitude`` is its standard deviation."""
    wave = np.random.default_rng(seed).normal(
        0.0, amplitude, int(sample_rate * duration_s)
    )
    return (np.clip(wave, -1.0, 1.0) * PCM16.INT_PEAK).astype(PCM16.IntType)


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
