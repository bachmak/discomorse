import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import sine_pcm

from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.pcm16 import PCM16

_TARGET_RATE = 8_000
_PUSH_BYTES = 2048
# The polyphase filter rings at both ends of a stream; ignore those samples.
_EDGE_SAMPLES = 1_000


def _push_all(resampler: Resampler, pcm: bytes) -> bytes:
    pushed = b"".join(
        resampler.push(pcm[offset : offset + _PUSH_BYTES])
        for offset in range(0, len(pcm), _PUSH_BYTES)
    )
    return pushed + resampler.flush()


def _resample_tone(
    source_rate: int, freq_hz: float, duration_s: float = 1.0
) -> npt.NDArray[PCM16.IntType]:
    resampler = Resampler(source_rate=source_rate, target_rate=_TARGET_RATE)
    pcm = sine_pcm(freq_hz, duration_s, source_rate).tobytes()
    return np.frombuffer(_push_all(resampler, pcm), dtype=PCM16.IntType)


def _dominant_frequency(samples: npt.NDArray[PCM16.IntType]) -> float:
    spectrum = np.abs(np.fft.rfft(samples.astype(np.float64)))
    bins = np.fft.rfftfreq(len(samples), 1 / _TARGET_RATE)
    return float(bins[int(np.argmax(spectrum))])


_SOURCE_RATES = [
    pytest.param(_TARGET_RATE, id="passthrough"),
    pytest.param(48_000, id="downsample"),
    pytest.param(44_100, id="downsample-fractional-ratio"),
    pytest.param(4_000, id="upsample"),
]


@pytest.mark.parametrize("source_rate", _SOURCE_RATES)
def test_resampler_emits_one_second_of_target_rate_int16(source_rate: int) -> None:
    samples = _resample_tone(source_rate, freq_hz=440)

    assert samples.dtype == PCM16.IntType
    assert abs(len(samples) - _TARGET_RATE) <= 1


@pytest.mark.parametrize("source_rate", _SOURCE_RATES)
def test_resampler_preserves_tone_frequency(source_rate: int) -> None:
    samples = _resample_tone(source_rate, freq_hz=440)

    assert _dominant_frequency(samples) == pytest.approx(440, abs=2)


def test_resampler_filters_content_above_the_target_nyquist() -> None:
    samples = _resample_tone(48_000, freq_hz=6_000)

    assert np.abs(samples[_EDGE_SAMPLES:-_EDGE_SAMPLES]).max() < 100


def test_resampler_flush_drains_the_filter_tail() -> None:
    resampler = Resampler(source_rate=48_000, target_rate=_TARGET_RATE)

    pushed = resampler.push(sine_pcm(440, 1.0, 48_000).tobytes())
    tail = resampler.flush()

    assert tail
    assert abs(len(pushed + tail) // PCM16.BYTES_PER_SAMPLE - _TARGET_RATE) <= 1


def test_resampler_flush_is_empty_without_input() -> None:
    assert Resampler(source_rate=48_000, target_rate=_TARGET_RATE).flush() == b""
