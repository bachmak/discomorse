import datetime
import math

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import EPOCH, chirp_pcm, noise_pcm, sine_pcm
from carrier_fixtures import (
    BIN_WIDTH_HZ,
    CARRIER_HZ,
    FRAME_SECONDS,
    HOLD_SECONDS,
    LOCK_SECONDS,
    RIVAL_HZ,
    SAMPLE_RATE,
    analyze,
    seconds_since_epoch,
    spectrum,
    track,
)
from limiter_fixtures import limit

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import CarrierSample, Tone, ToneSpectrum

_DRIFT = (600.0, 662.5, 725.0, 787.5)
_DRIFT_STEP_S = 1.0
_CARRIER_MAGNITUDE = 1.0
_SPECTRUM_STEP_S = 0.01
_SIGHTINGS_TO_LOCK = math.ceil(LOCK_SECONDS / _SPECTRUM_STEP_S) + 1
_SWEEP_START_HZ = 600.0
_SWEEP_END_HZ = 900.0
_SWEEP_SECONDS = 0.5
_SWEEP_HZ_PER_S = (_SWEEP_END_HZ - _SWEEP_START_HZ) / _SWEEP_SECONDS
# The carrier can only be read to the nearest bin, and one frame smears the
# sweep over the ground it covers while the frame is open.
_SWEEP_TOLERANCE_HZ = BIN_WIDTH_HZ / 2 + _SWEEP_HZ_PER_S * FRAME_SECONDS


def _tone(freq_hz: float, amplitude: float = 0.5) -> npt.NDArray[PCM16.IntType]:
    return sine_pcm(freq_hz, 0.1, SAMPLE_RATE, amplitude)


def _sweep() -> npt.NDArray[PCM16.IntType]:
    return chirp_pcm(_SWEEP_START_HZ, _SWEEP_END_HZ, _SWEEP_SECONDS, SAMPLE_RATE)


async def _tracked(
    samples: npt.NDArray[PCM16.IntType],
) -> tuple[CarrierSample, ...]:
    """The carrier read off real spectrums, cut the way the pipeline cuts them."""
    tracked = track(await limit(await analyze(samples)))
    assert tracked
    return tracked


def _swept_hz(ts: datetime.datetime) -> float:
    return _SWEEP_START_HZ + _SWEEP_HZ_PER_S * seconds_since_epoch(ts)


def _is_locked_at(index: int, step_seconds: float) -> bool:
    """Whether the spectrum at ``index`` closes a long enough run of sightings."""
    return index * step_seconds >= LOCK_SECONDS


def _keyed_then_silent_against(
    rival_magnitude: float, gap_seconds: float
) -> tuple[ToneSpectrum, ...]:
    """The carrier keys long enough to lock, then falls silent while a rival calls."""
    bins = [{CARRIER_HZ: _CARRIER_MAGNITUDE, RIVAL_HZ: 0.0}] * _SIGHTINGS_TO_LOCK
    bins += [{CARRIER_HZ: 0.0, RIVAL_HZ: rival_magnitude}] * int(
        gap_seconds / _SPECTRUM_STEP_S
    )
    return tuple(
        spectrum(spectrum_bins, at_second=index * _SPECTRUM_STEP_S)
        for index, spectrum_bins in enumerate(bins)
    )


@pytest.mark.parametrize(
    "bins, want_frequency, want_magnitude",
    [
        pytest.param({500.0: 0.2, 700.0: 0.9, 900.0: 0.3}, 700.0, 0.9, id="loudest"),
        pytest.param({400.0: 0.7, 1_200.0: 0.6}, 400.0, 0.7, id="lowest-bin-loudest"),
        pytest.param({400.0: 0.6, 1_200.0: 0.7}, 1_200.0, 0.7, id="top-bin-loudest"),
        pytest.param({700.0: 0.0, 800.0: 0.0}, 700.0, 0.0, id="silence-still-tracked"),
    ],
)
def test_source_reads_the_carrier_off_the_loudest_bin_it_is_given(
    bins: dict[float, float], want_frequency: float, want_magnitude: float
) -> None:
    samples = track((spectrum(bins),))

    assert samples == (
        CarrierSample(
            tone=Tone(frequency=want_frequency, magnitude=want_magnitude, ts=EPOCH),
            is_locked=False,
        ),
    )


def test_source_follows_a_drifting_carrier() -> None:
    spectrums = tuple(
        spectrum(
            {400.0: 0.1, frequency: 0.8, 1_200.0: 0.1},
            at_second=index * _DRIFT_STEP_S,
        )
        for index, frequency in enumerate(_DRIFT)
    )

    samples = track(spectrums)

    assert samples == tuple(
        CarrierSample(
            tone=Tone(frequency=frequency, magnitude=0.8, ts=drifted.ts),
            is_locked=_is_locked_at(index, _DRIFT_STEP_S),
        )
        for index, (drifted, frequency) in enumerate(
            zip(spectrums, _DRIFT, strict=True)
        )
    )


@pytest.mark.parametrize(
    "rival_magnitude, gap_seconds, want_frequency",
    [
        pytest.param(
            _CARRIER_MAGNITUDE / 2,
            HOLD_SECONDS / 2,
            CARRIER_HZ,
            id="quieter-rival-cannot-take-a-pause-for-a-vacancy",
        ),
        pytest.param(
            _CARRIER_MAGNITUDE / 2,
            HOLD_SECONDS * 2,
            RIVAL_HZ,
            id="quieter-rival-wins-once-the-carrier-has-left-the-air",
        ),
        pytest.param(
            _CARRIER_MAGNITUDE * 2,
            HOLD_SECONDS / 2,
            RIVAL_HZ,
            id="louder-rival-takes-the-lock-straight-away",
        ),
    ],
)
def test_source_defends_a_locked_carrier_while_it_is_only_pausing(
    rival_magnitude: float, gap_seconds: float, want_frequency: float
) -> None:
    spectrums = _keyed_then_silent_against(rival_magnitude, gap_seconds)

    samples = track(spectrums)

    assert samples[-1].tone.frequency == want_frequency


async def test_source_locks_onto_a_played_tone() -> None:
    samples = await _tracked(_tone(750.0))

    assert all(sample.tone.frequency == 750.0 for sample in samples)
    assert [sample.tone.magnitude for sample in samples] == pytest.approx(
        [0.5] * len(samples), rel=0.02
    )


async def test_source_follows_a_tone_sweeping_through_real_spectrums() -> None:
    samples = await _tracked(_sweep())

    assert [sample.tone.frequency for sample in samples] == pytest.approx(
        [_swept_hz(sample.tone.ts) for sample in samples], abs=_SWEEP_TOLERANCE_HZ
    )


async def test_source_reads_a_sweep_as_a_carrier_that_never_falls_silent() -> None:
    samples = await _tracked(_sweep())

    assert all(sample.tone.magnitude > 0.4 for sample in samples)


async def test_source_keeps_noise_far_below_the_magnitude_of_a_tone() -> None:
    noise = await _tracked(noise_pcm(0.1, SAMPLE_RATE))
    tone = await _tracked(_tone(750.0))

    assert max(sample.tone.magnitude for sample in noise) < 0.1 * min(
        sample.tone.magnitude for sample in tone
    )


async def test_source_never_sees_a_louder_tone_the_limiter_cut_away() -> None:
    mixed = _tone(750.0, amplitude=0.2) + _tone(2_000.0, amplitude=0.7)

    samples = await _tracked(np.asarray(mixed, dtype=PCM16.IntType))

    assert all(sample.tone.frequency == 750.0 for sample in samples)
