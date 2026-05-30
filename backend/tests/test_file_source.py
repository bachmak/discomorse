"""Tests for FileSource: chunking, resampling, downmixing, and fidelity.

Audio is synthesized in-memory (see ``audio_fixtures``). Where input is
already at the target rate/width/channels, pydub short-circuits the
conversions, so byte counts are exact. Where resampling happens, assertions
use tolerances — resampled audio is never sample-exact — and check the
frequency domain instead.
"""

import numpy as np
from audio_fixtures import sine_pcm, sine_wav, wav_bytes

from morse_decoder.audio.file_source import FileSource
from morse_decoder.config import AudioSettings

_TARGET_RATE = 8000
_SAMPLE_WIDTH = 2  # bytes per Int16 sample


def _conformed(samples: np.ndarray, chunk_size: int) -> FileSource:
    """A FileSource over already-conformed PCM (no resampling on decode)."""
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=chunk_size)
    return FileSource(wav_bytes(samples, _TARGET_RATE), audio, fmt="wav")


async def _collect(source: FileSource) -> list[bytes]:
    return [chunk async for chunk in source.stream()]


async def test_stream_reassembles_to_original_pcm() -> None:
    """Chunks rejoin to the exact decoded PCM, in order and lossless."""
    samples = sine_pcm(800, 0.625, _TARGET_RATE)  # 5000 samples
    source = _conformed(samples, chunk_size=2048)

    rejoined = b"".join(await _collect(source))

    assert rejoined == samples.tobytes()


async def test_chunks_are_full_except_the_last() -> None:
    samples = sine_pcm(800, 0.625, _TARGET_RATE)  # 5000 samples -> 3 chunks
    source = _conformed(samples, chunk_size=2048)
    chunk_bytes = 2048 * _SAMPLE_WIDTH

    chunks = await _collect(source)

    assert all(len(chunk) == chunk_bytes for chunk in chunks[:-1])
    assert 0 < len(chunks[-1]) <= chunk_bytes


async def test_exact_multiple_yields_no_partial_chunk() -> None:
    samples = sine_pcm(800, 0.5, _TARGET_RATE)  # 4000 samples
    source = _conformed(samples, chunk_size=1000)
    chunk_bytes = 1000 * _SAMPLE_WIDTH

    chunks = await _collect(source)

    assert len(chunks) == 4
    assert all(len(chunk) == chunk_bytes for chunk in chunks)


async def test_input_smaller_than_one_chunk_yields_single_chunk() -> None:
    samples = sine_pcm(800, 0.0125, _TARGET_RATE)  # 100 samples
    source = _conformed(samples, chunk_size=2048)

    chunks = await _collect(source)

    assert len(chunks) == 1
    assert len(chunks[0]) == 100 * _SAMPLE_WIDTH


async def test_resamples_to_target_rate() -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=2048)
    source = FileSource(sine_wav(800, 1.0, 44100), audio, fmt="wav")

    sample_count = len(b"".join(await _collect(source))) // _SAMPLE_WIDTH

    assert abs(sample_count - _TARGET_RATE) <= 4  # ~1s at the target rate


async def test_downmixes_stereo_to_mono() -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=2048)
    source = FileSource(sine_wav(800, 0.2, _TARGET_RATE, channels=2), audio, fmt="wav")

    sample_count = len(b"".join(await _collect(source))) // _SAMPLE_WIDTH

    assert sample_count == int(_TARGET_RATE * 0.2)  # 1600 mono samples


async def test_preserves_tone_frequency() -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=2048)
    source = FileSource(sine_wav(770, 0.5, 44100), audio, fmt="wav")

    pcm = np.frombuffer(b"".join(await _collect(source)), dtype=np.int16)
    spectrum = np.abs(np.fft.rfft(pcm.astype(np.float64)))
    freqs = np.fft.rfftfreq(pcm.size, 1 / _TARGET_RATE)
    peak_hz = float(freqs[int(spectrum.argmax())])

    assert abs(peak_hz - 770) < 20
