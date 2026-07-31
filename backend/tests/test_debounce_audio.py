"""The debounced key read off spectrums of synthesized audio, not hand-built keys."""

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import noise_pcm, silence_pcm, sine_pcm
from carrier_fixtures import SAMPLE_RATE, analyze
from debounce_fixtures import edges
from tone_detecting_fixtures import ReadKey, read_key
from tone_fixtures import DIT_SECONDS, KEY_DOWN_AMPLITUDE, TONE_HZ

from morse_decoder.audio.pcm16 import PCM16

_MARK_SECONDS = 0.1
_NOISE_AMPLITUDE = 0.05


def _torn_pcm(
    gap_seconds: float, noise_amplitude: float = 0.0
) -> npt.NDArray[PCM16.IntType]:
    """One mark of a tone cut in two by ``gap_seconds`` of key-up."""
    half = sine_pcm(TONE_HZ, _MARK_SECONDS, SAMPLE_RATE, KEY_DOWN_AMPLITUDE)
    keyed = np.concatenate((half, silence_pcm(gap_seconds, SAMPLE_RATE), half))
    if not noise_amplitude:
        return keyed
    floor = noise_pcm(len(keyed) / SAMPLE_RATE, SAMPLE_RATE, noise_amplitude)
    return np.asarray(keyed + floor, dtype=PCM16.IntType)


async def _read(samples: npt.NDArray[PCM16.IntType]) -> ReadKey:
    """The key as it is read off ``samples``, before and after the debouncer."""
    return read_key((await analyze(samples)).spectrums)


@pytest.mark.parametrize(
    "noise_amplitude",
    [
        pytest.param(0.0, id="a-clean-signal"),
        pytest.param(_NOISE_AMPLITUDE, id="a-noise-floor-under-the-signal"),
    ],
)
@pytest.mark.parametrize(
    "gap_seconds",
    [
        pytest.param(0.012, id="a-dropout-of-12ms"),
        pytest.param(0.02, id="a-dropout-of-20ms"),
    ],
)
async def test_a_mark_torn_by_a_dropout_reads_back_as_one_mark(
    gap_seconds: float, noise_amplitude: float
) -> None:
    key = await _read(_torn_pcm(gap_seconds, noise_amplitude))

    assert edges(key.raw) == 3
    assert edges(key.debounced) == 1


@pytest.mark.parametrize(
    "noise_amplitude",
    [
        pytest.param(0.0, id="a-clean-signal"),
        pytest.param(_NOISE_AMPLITUDE, id="a-noise-floor-under-the-signal"),
    ],
)
async def test_the_gap_between_two_elements_lives_through_the_debouncer(
    noise_amplitude: float,
) -> None:
    key = await _read(_torn_pcm(DIT_SECONDS, noise_amplitude))

    assert edges(key.raw) == edges(key.debounced) == 3
    assert key.debounced[-1]


async def test_a_noise_floor_on_its_own_never_keys_the_debounced_line() -> None:
    floor = noise_pcm(_MARK_SECONDS * 2, SAMPLE_RATE, _NOISE_AMPLITUDE)

    key = await _read(floor)

    assert not any(key.debounced)
