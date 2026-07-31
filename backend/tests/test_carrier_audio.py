"""Carrier tracking over spectrums of synthesized audio, not hand-built bins."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import noise_pcm, sine_pcm
from carrier_fixtures import (
    FRAME_SECONDS,
    HOP_SECONDS,
    LOCK_SECONDS,
    MIN_MAGNITUDE,
    SAMPLE_RATE,
    analyze,
    first_locked_index,
    frequencies,
    lock_flags,
    seconds_since_epoch,
    track,
)

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.stages.tone_detector.impl.dto import CarrierSample

_TONE_HZ = 750.0
_INTRUDER_HZ = 1_000.0
_BURST_SECONDS = 0.1
_KEY_DOWN_AMPLITUDE = 0.5
_FRAMES_TO_LOCK = round(LOCK_SECONDS / HOP_SECONDS)


@dataclass(frozen=True)
class _Phase:
    """A stretch of the keyed signal and the levels its frames must report."""

    start_s: float
    end_s: float
    lowest_magnitude: float
    highest_magnitude: float

    def covers(self, sample: CarrierSample) -> bool:
        """Whether the sample's frame lies wholly inside this phase."""
        centre = seconds_since_epoch(sample.tone.ts)
        return (
            centre - FRAME_SECONDS / 2 >= self.start_s
            and centre + FRAME_SECONDS / 2 <= self.end_s
        )

    def holds(self, sample: CarrierSample) -> bool:
        return self.lowest_magnitude <= sample.tone.magnitude <= self.highest_magnitude


_KEY_DOWN = (0.45, 0.55)
_KEY_UP = (0.0, 0.001)
_PHASES = (
    _Phase(0.0, _BURST_SECONDS, *_KEY_DOWN),
    _Phase(_BURST_SECONDS, _BURST_SECONDS * 2, *_KEY_UP),
    _Phase(_BURST_SECONDS * 2, _BURST_SECONDS * 3, *_KEY_DOWN),
)


def _silence(seconds: float) -> npt.NDArray[PCM16.IntType]:
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=PCM16.IntType)


def _keyed_pcm(noise_amplitude: float = 0.0) -> npt.NDArray[PCM16.IntType]:
    """Two keyed bursts of one tone with the key up in between."""
    burst = sine_pcm(_TONE_HZ, _BURST_SECONDS, SAMPLE_RATE, _KEY_DOWN_AMPLITUDE)
    keyed = np.concatenate((burst, _silence(_BURST_SECONDS), burst))
    if not noise_amplitude:
        return keyed
    floor = noise_pcm(_BURST_SECONDS * 3, SAMPLE_RATE, noise_amplitude)
    return np.asarray(keyed + floor, dtype=PCM16.IntType)


async def _tracked(samples: npt.NDArray[PCM16.IntType]) -> tuple[CarrierSample, ...]:
    return track((await analyze(samples)).spectrums)


@pytest.mark.parametrize(
    "noise_amplitude",
    [
        pytest.param(0.0, id="a-clean-signal"),
        pytest.param(0.02, id="a-noise-floor-under-the-signal"),
    ],
)
async def test_a_keyed_carrier_holds_its_frequency_through_the_gaps(
    noise_amplitude: float,
) -> None:
    samples = await _tracked(_keyed_pcm(noise_amplitude))

    assert first_locked_index(samples) == _FRAMES_TO_LOCK
    assert all(lock_flags(samples)[_FRAMES_TO_LOCK:])
    assert set(frequencies(samples)) == {_TONE_HZ}


@pytest.mark.parametrize(
    "phase", [pytest.param(phase, id=f"from-{phase.start_s}s") for phase in _PHASES]
)
async def test_a_keyed_carrier_reports_the_level_of_every_phase(phase: _Phase) -> None:
    samples = await _tracked(_keyed_pcm())

    inside = tuple(sample for sample in samples if phase.covers(sample))
    assert inside
    assert all(phase.holds(sample) for sample in inside)


async def test_a_louder_tone_inside_the_window_steals_the_lock() -> None:
    half = _BURST_SECONDS * 1.5
    quiet = sine_pcm(_TONE_HZ, half, SAMPLE_RATE, amplitude=0.15)
    loud = sine_pcm(_INTRUDER_HZ, half, SAMPLE_RATE, amplitude=0.6)

    samples = await _tracked(np.concatenate((quiet, loud)))

    before = _Phase(0.0, half, 0.0, 1.0)
    assert {sample.tone.frequency for sample in samples if before.covers(sample)} == {
        _TONE_HZ
    }
    assert samples[-1].tone.frequency == _INTRUDER_HZ
    assert samples[-1].is_locked


async def test_a_tone_below_the_lock_threshold_is_followed_but_never_locked() -> None:
    faint = sine_pcm(
        _TONE_HZ, _BURST_SECONDS * 3, SAMPLE_RATE, amplitude=MIN_MAGNITUDE / 2
    )

    samples = await _tracked(faint)

    assert not any(lock_flags(samples))
    assert set(frequencies(samples)) == {_TONE_HZ}


async def test_a_noise_floor_on_its_own_never_locks() -> None:
    samples = await _tracked(noise_pcm(_BURST_SECONDS * 3, SAMPLE_RATE, amplitude=0.02))

    assert samples
    assert not any(lock_flags(samples))
