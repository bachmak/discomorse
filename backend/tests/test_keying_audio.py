"""The key read off spectrums of synthesized audio, not hand-built readings."""

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import noise_pcm, silence_pcm, sine_pcm
from carrier_fixtures import (
    FRAME_SECONDS,
    LOCK_SECONDS,
    MIN_MAGNITUDE,
    SAMPLE_RATE,
    Phase,
    analyze,
    track,
)
from keying_fixtures import key_off, keys

from morse_decoder.audio.pcm16 import PCM16

_TONE_HZ = 750.0
_BURST_SECONDS = 0.1
_KEY_DOWN_AMPLITUDE = 0.5
_LOCKED_S = LOCK_SECONDS + FRAME_SECONDS

_PHASES = (
    (Phase(_LOCKED_S, _BURST_SECONDS), True),
    (Phase(_BURST_SECONDS, _BURST_SECONDS * 2), False),
    (Phase(_BURST_SECONDS * 2, _BURST_SECONDS * 3), True),
)


def _keyed_pcm(noise_amplitude: float = 0.0) -> npt.NDArray[PCM16.IntType]:
    """Two keyed bursts of one tone with the key up in between."""
    burst = sine_pcm(_TONE_HZ, _BURST_SECONDS, SAMPLE_RATE, _KEY_DOWN_AMPLITUDE)
    keyed = np.concatenate((burst, silence_pcm(_BURST_SECONDS, SAMPLE_RATE), burst))
    if not noise_amplitude:
        return keyed
    floor = noise_pcm(_BURST_SECONDS * 3, SAMPLE_RATE, noise_amplitude)
    return np.asarray(keyed + floor, dtype=PCM16.IntType)


async def _keyed(samples: npt.NDArray[PCM16.IntType]) -> tuple[bool, ...]:
    return keys(key_off((await analyze(samples)).spectrums))


async def _keyed_inside(
    samples: npt.NDArray[PCM16.IntType], phase: Phase
) -> tuple[bool, ...]:
    """The key over the frames that lie wholly inside ``phase``."""
    spectrums = (await analyze(samples)).spectrums
    return tuple(
        flag
        for flag, spectrum in zip(keys(key_off(spectrums)), spectrums, strict=True)
        if phase.covers(spectrum.ts)
    )


@pytest.mark.parametrize(
    "noise_amplitude",
    [
        pytest.param(0.0, id="a-clean-signal"),
        pytest.param(0.02, id="a-noise-floor-under-the-signal"),
        pytest.param(0.05, id="a-loud-noise-floor-under-the-signal"),
    ],
)
@pytest.mark.parametrize(
    "phase, want",
    [pytest.param(phase, want, id=f"from-{phase.start_s}s") for phase, want in _PHASES],
)
async def test_the_key_reads_back_the_bursts_it_was_keyed_with(
    noise_amplitude: float, phase: Phase, want: bool
) -> None:
    flags = await _keyed_inside(_keyed_pcm(noise_amplitude), phase)

    assert flags
    assert all(flag is want for flag in flags)


async def test_the_key_stays_up_until_the_carrier_is_locked() -> None:
    spectrums = (await analyze(_keyed_pcm())).spectrums

    flags = keys(key_off(spectrums))
    carriers = track(spectrums)

    assert not any(
        flag
        for flag, carrier in zip(flags, carriers, strict=True)
        if not carrier.is_locked
    )


async def test_a_tone_too_faint_to_lock_never_keys_the_line() -> None:
    faint = sine_pcm(
        _TONE_HZ, _BURST_SECONDS * 3, SAMPLE_RATE, amplitude=MIN_MAGNITUDE / 2
    )

    assert not any(await _keyed(faint))


async def test_a_noise_floor_on_its_own_never_keys_the_line() -> None:
    floor = noise_pcm(_BURST_SECONDS * 3, SAMPLE_RATE, amplitude=0.05)

    assert not any(await _keyed(floor))
