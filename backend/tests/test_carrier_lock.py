"""Acquiring the lock: what the source demands before it stops searching."""

import math

import pytest
from carrier_fixtures import (
    CARRIER_HZ,
    HOLD_SECONDS,
    LOCK_SECONDS,
    LOUD,
    MIN_MAGNITUDE,
    RIVAL_HZ,
    STEP_S,
    TOLERANCE_HZ,
    SpectrumTimeline,
    frequencies,
    lock_flags,
    magnitudes,
    source,
    spectrums_at,
    track,
)

from morse_decoder.config import CarrierSourceSettings
from morse_decoder.pipeline.dto import CarrierSample, Tone

_SPECTRUMS = 12
_DRIFT_SPECTRUMS = 6
_DRIFT_START_HZ = 500.0


@pytest.mark.parametrize(
    "step_seconds",
    [
        pytest.param(LOCK_SECONDS / 10, id="ten-spectrums-per-lock-time"),
        pytest.param(LOCK_SECONDS / 2, id="two-spectrums-per-lock-time"),
        pytest.param(LOCK_SECONDS, id="one-spectrum-per-lock-time"),
        pytest.param(LOCK_SECONDS * 3, id="one-spectrum-per-three-lock-times"),
    ],
)
async def test_the_lock_reaches_back_over_the_whole_run_that_closed_it(
    step_seconds: float,
) -> None:
    """A run is carrier from its first frame on, not from the frame that proved it.

    The frames that make the lock are the opening of the signal that closed it,
    so the lock time costs the run nothing once the verdict is in.
    """
    spectrums = (
        SpectrumTimeline(step_seconds).add({CARRIER_HZ: LOUD}, _SPECTRUMS).build()
    )

    samples = await track(spectrums)

    assert lock_flags(samples) == (True,) * _SPECTRUMS


@pytest.mark.parametrize(
    "lock_seconds, want_locked",
    [
        pytest.param(STEP_S / 10, True, id="far-shorter-than-one-spectrum"),
        pytest.param(STEP_S, True, id="exactly-one-spectrum"),
        pytest.param(STEP_S * 2, True, id="two-spectrums"),
        pytest.param(STEP_S * _SPECTRUMS, False, id="longer-than-the-stream"),
    ],
)
async def test_only_a_run_that_reaches_the_lock_time_becomes_the_carrier(
    lock_seconds: float, want_locked: bool
) -> None:
    settings = CarrierSourceSettings(carrier_lock_seconds=lock_seconds)
    spectrums = SpectrumTimeline().add({CARRIER_HZ: LOUD}, _SPECTRUMS).build()

    samples = await track(spectrums, carrier_source=source(settings))

    assert any(lock_flags(samples)) == want_locked


async def test_the_first_spectrum_can_never_close_the_lock_on_its_own() -> None:
    """One sighting is no run, however little time the lock asks for."""
    settings = CarrierSourceSettings(carrier_lock_seconds=STEP_S / 10)
    spectrums = SpectrumTimeline().add({CARRIER_HZ: LOUD}, 1).build()

    samples = await track(spectrums, carrier_source=source(settings))

    assert lock_flags(samples) == (False,)


@pytest.mark.parametrize(
    "magnitude, want_locked",
    [
        pytest.param(LOUD, True, id="far-above-the-threshold"),
        pytest.param(MIN_MAGNITUDE, True, id="exactly-at-the-threshold"),
        pytest.param(math.nextafter(MIN_MAGNITUDE, 0.0), False, id="a-hair-below"),
        pytest.param(MIN_MAGNITUDE / 2, False, id="half-the-threshold"),
        pytest.param(0.0, False, id="silence"),
    ],
)
async def test_only_a_level_above_the_lock_threshold_can_be_locked(
    magnitude: float, want_locked: bool
) -> None:
    spectrums = SpectrumTimeline().add({CARRIER_HZ: magnitude}, _SPECTRUMS).build()

    samples = await track(spectrums)

    assert any(lock_flags(samples)) == want_locked
    assert magnitudes(samples) == (magnitude,) * _SPECTRUMS


@pytest.mark.parametrize(
    "stride_hz, want_locked",
    [
        pytest.param(0.0, True, id="a-steady-carrier"),
        pytest.param(TOLERANCE_HZ / 4, True, id="well-inside-the-band"),
        pytest.param(TOLERANCE_HZ / 2, True, id="reaching-the-edge-as-the-lock-closes"),
        pytest.param(TOLERANCE_HZ / 2 + 1.0, False, id="leaving-the-band-too-early"),
        pytest.param(TOLERANCE_HZ + 1.0, False, id="hopping-past-the-band"),
    ],
)
async def test_the_run_survives_only_drift_that_stays_inside_the_tolerance_band(
    stride_hz: float, want_locked: bool
) -> None:
    """The band is pinned to the first sighting, so drift accumulates against it."""
    timeline = SpectrumTimeline()
    for index in range(_DRIFT_SPECTRUMS):
        timeline.add({_DRIFT_START_HZ + index * stride_hz: LOUD})

    samples = await track(timeline.build())

    assert lock_flags(samples) == (want_locked,) * _DRIFT_SPECTRUMS


async def test_the_lock_lands_where_the_carrier_is_now_not_where_it_began() -> None:
    drift = tuple(_DRIFT_START_HZ + index * TOLERANCE_HZ / 2 for index in range(4))
    timeline = SpectrumTimeline()
    for frequency in drift:
        timeline.add({frequency: LOUD})

    samples = await track(timeline.build())

    assert all(lock_flags(samples))
    assert frequencies(samples) == drift
    assert samples[2].tone.frequency != drift[0]


@pytest.mark.parametrize(
    "bins, other_bins",
    [
        pytest.param(
            {_DRIFT_START_HZ: LOUD}, {RIVAL_HZ: LOUD}, id="the-peak-hops-between-tones"
        ),
        pytest.param(
            {CARRIER_HZ: LOUD}, {CARRIER_HZ: 0.0}, id="the-carrier-is-keyed-in-bursts"
        ),
        pytest.param(
            {CARRIER_HZ: LOUD},
            {CARRIER_HZ: MIN_MAGNITUDE / 2},
            id="the-carrier-dips-below-the-threshold",
        ),
    ],
)
async def test_a_run_broken_every_other_spectrum_never_locks(
    bins: dict[float, float], other_bins: dict[float, float]
) -> None:
    spectrums = SpectrumTimeline().alternate(bins, other_bins, cycles=10, run=1).build()

    assert not any(lock_flags(await track(spectrums)))


@pytest.mark.parametrize(
    "seconds, want_lock_flags",
    [
        pytest.param(
            (0.0, 0.0, 0.0), (False, False, False), id="a-clock-standing-still"
        ),
        pytest.param((1.0, 0.5, 0.0), (False, False, False), id="stamps-running-back"),
        pytest.param(
            (0.0, LOCK_SECONDS, LOCK_SECONDS * 2),
            (True, True, True),
            id="one-lock-time-per-step",
        ),
        pytest.param((0.0, 60.0), (True, True), id="a-minute-long-gap-in-the-stream"),
    ],
)
async def test_the_lock_follows_the_stamps_the_spectrums_carry(
    seconds: tuple[float, ...], want_lock_flags: tuple[bool, ...]
) -> None:
    spectrums = spectrums_at({CARRIER_HZ: LOUD}, seconds)

    assert lock_flags(await track(spectrums)) == want_lock_flags


async def test_a_stream_of_silence_never_locks_however_long_it_runs() -> None:
    spectrums = (
        SpectrumTimeline()
        .hold({CARRIER_HZ: 0.0, RIVAL_HZ: 0.0}, seconds=HOLD_SECONDS * 2)
        .build()
    )

    samples = await track(spectrums)

    assert not any(lock_flags(samples))
    assert set(frequencies(samples)) == {CARRIER_HZ}
    assert set(magnitudes(samples)) == {0.0}


async def test_while_searching_the_loudest_bin_is_passed_through_unchanged() -> None:
    loud_low = {_DRIFT_START_HZ: LOUD, RIVAL_HZ: 0.2}
    loud_high = {_DRIFT_START_HZ: 0.2, RIVAL_HZ: LOUD}
    spectrums = (
        SpectrumTimeline().alternate(loud_low, loud_high, cycles=5, run=1).build()
    )

    samples = await track(spectrums)

    assert samples == tuple(
        CarrierSample(
            tone=Tone(
                frequency=_DRIFT_START_HZ if index % 2 == 0 else RIVAL_HZ,
                magnitude=LOUD,
                ts=spectrum.ts,
            ),
            is_locked=False,
        )
        for index, spectrum in enumerate(spectrums)
    )
