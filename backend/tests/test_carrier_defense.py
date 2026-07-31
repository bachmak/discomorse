"""Holding the lock: what a locked carrier survives, and what unseats it."""

import pytest
from carrier_fixtures import (
    CARRIER_HZ,
    HOLD_SECONDS,
    LOCK_PHASE_SPECTRUMS,
    LOCK_SECONDS,
    LOUD,
    MIN_MAGNITUDE,
    RIVAL_HZ,
    SILENT,
    STEP_S,
    TOLERANCE_HZ,
    frequencies,
    lock_flags,
    locking_timeline,
    magnitudes,
    spectrums_at,
    track,
)

_CONTEST_SECONDS = LOCK_SECONDS * 3
_CONTEST_SPECTRUMS = round(_CONTEST_SECONDS / STEP_S)
_FADED = LOUD * 0.2
_QUIET_RIVAL = LOUD * 0.5
_LOUD_RIVAL = LOUD * 1.5


def _after_lock(samples: tuple[float, ...]) -> tuple[float, ...]:
    return samples[LOCK_PHASE_SPECTRUMS:]


@pytest.mark.parametrize(
    "stride_hz",
    [
        pytest.param(TOLERANCE_HZ, id="steps-of-a-full-tolerance"),
        pytest.param(TOLERANCE_HZ * 0.9, id="steps-just-inside-the-tolerance"),
    ],
)
@pytest.mark.parametrize(
    "magnitude",
    [
        pytest.param(LOUD, id="a-loud-carrier"),
        pytest.param(MIN_MAGNITUDE, id="a-barely-credible-carrier"),
    ],
)
def test_a_locked_carrier_follows_steps_inside_the_tolerance(
    stride_hz: float, magnitude: float
) -> None:
    walk = tuple(CARRIER_HZ + step * stride_hz for step in range(1, 6))
    timeline = locking_timeline()
    for frequency in walk:
        timeline.add({frequency: magnitude})

    samples = track(timeline.build())

    assert _after_lock(frequencies(samples)) == walk
    assert _after_lock(magnitudes(samples)) == (magnitude,) * len(walk)
    assert all(lock_flags(samples)[LOCK_PHASE_SPECTRUMS:])


@pytest.mark.parametrize(
    "rival_magnitude, want_frequencies",
    [
        pytest.param(
            _LOUD_RIVAL,
            (CARRIER_HZ, CARRIER_HZ) + (RIVAL_HZ,) * 4,
            id="a-louder-rival-waits-out-the-lock-time",
        ),
        pytest.param(
            LOUD,
            (CARRIER_HZ, CARRIER_HZ) + (RIVAL_HZ,) * 4,
            id="an-equally-loud-rival-still-wins",
        ),
        pytest.param(
            LOUD * 0.99,
            (CARRIER_HZ,) * _CONTEST_SPECTRUMS,
            id="a-hair-quieter-and-the-rival-never-gets-in",
        ),
    ],
)
def test_a_rival_needs_the_lock_time_before_it_can_take_the_carrier(
    rival_magnitude: float, want_frequencies: tuple[float, ...]
) -> None:
    contested = {CARRIER_HZ: _FADED, RIVAL_HZ: rival_magnitude}
    spectrums = locking_timeline().hold(contested, _CONTEST_SECONDS).build()

    samples = track(spectrums)

    assert _after_lock(frequencies(samples)) == want_frequencies
    assert all(lock_flags(samples)[LOCK_PHASE_SPECTRUMS:])


def test_a_rival_must_beat_the_loudest_the_carrier_has_ever_been() -> None:
    """The carrier fades below the rival, but never below its own best level."""
    contested = {CARRIER_HZ: _FADED, RIVAL_HZ: _QUIET_RIVAL}
    spectrums = locking_timeline().hold(contested, HOLD_SECONDS / 2).build()

    samples = track(spectrums)

    assert set(_after_lock(frequencies(samples))) == {CARRIER_HZ}
    assert set(_after_lock(magnitudes(samples))) == {_FADED}


@pytest.mark.parametrize(
    "contest_seconds, want_frequency",
    [
        pytest.param(HOLD_SECONDS, CARRIER_HZ, id="off-air-for-exactly-the-hold-time"),
        pytest.param(
            HOLD_SECONDS + LOCK_SECONDS,
            CARRIER_HZ,
            id="one-spectrum-short-of-the-takeover",
        ),
        pytest.param(
            HOLD_SECONDS + LOCK_SECONDS + STEP_S,
            RIVAL_HZ,
            id="past-the-hold-time-and-the-lock-time",
        ),
    ],
)
def test_a_quieter_rival_wins_only_once_the_carrier_has_been_off_air(
    contest_seconds: float, want_frequency: float
) -> None:
    contested = {CARRIER_HZ: 0.0, RIVAL_HZ: MIN_MAGNITUDE}
    spectrums = locking_timeline().hold(contested, contest_seconds).build()

    assert frequencies(track(spectrums))[-1] == want_frequency


@pytest.mark.parametrize(
    "run, want_frequency",
    [
        pytest.param(1, CARRIER_HZ, id="one-spectrum-at-a-time"),
        pytest.param(2, CARRIER_HZ, id="two-spectrums-at-a-time"),
        pytest.param(3, RIVAL_HZ, id="three-spectrums-make-one-lock-time"),
    ],
)
def test_a_rival_that_keeps_dropping_out_never_holds_on_long_enough(
    run: int, want_frequency: float
) -> None:
    calling = {CARRIER_HZ: 0.0, RIVAL_HZ: _LOUD_RIVAL}
    keyed = {CARRIER_HZ: LOUD, RIVAL_HZ: 0.0}
    spectrums = locking_timeline().alternate(calling, keyed, cycles=5, run=run).build()

    samples = track(spectrums)

    assert frequencies(samples)[-1] == want_frequency
    assert all(lock_flags(samples)[LOCK_PHASE_SPECTRUMS:])


def test_silence_alone_never_breaks_the_lock() -> None:
    """Only a competing signal can unseat the carrier — a key-up never does."""
    spectrums = locking_timeline().hold(SILENT, HOLD_SECONDS * 2).build()

    samples = track(spectrums)

    assert all(lock_flags(samples)[LOCK_PHASE_SPECTRUMS:])
    assert set(frequencies(samples)) == {CARRIER_HZ}
    assert set(_after_lock(magnitudes(samples))) == {0.0}


def test_a_locked_carrier_reports_its_own_level_not_the_loudest_bin() -> None:
    contested = {CARRIER_HZ: _FADED, RIVAL_HZ: _QUIET_RIVAL}
    spectrums = locking_timeline().hold(contested, LOCK_SECONDS).build()

    last = track(spectrums)[-1]

    assert last.tone.frequency == CARRIER_HZ
    assert last.tone.magnitude == _FADED
    assert last.is_locked


def test_each_takeover_resets_the_level_the_next_rival_must_beat() -> None:
    spectrums = (
        locking_timeline()
        .hold({CARRIER_HZ: 0.0, RIVAL_HZ: _LOUD_RIVAL}, LOCK_SECONDS * 2)
        .hold({CARRIER_HZ: LOUD, RIVAL_HZ: 0.0}, LOCK_SECONDS * 2)
        .hold({CARRIER_HZ: _LOUD_RIVAL * 1.2, RIVAL_HZ: 0.0}, LOCK_SECONDS * 2)
        .build()
    )

    tracked = frequencies(track(spectrums))

    phase_ends = tuple(tracked[LOCK_PHASE_SPECTRUMS * step - 1] for step in range(1, 5))
    assert phase_ends == (CARRIER_HZ, RIVAL_HZ, RIVAL_HZ, CARRIER_HZ)


def test_a_gap_in_the_stream_leaves_the_carrier_stale() -> None:
    """Nothing is heard for an hour, so the next rival only needs the lock time."""
    calling = {CARRIER_HZ: 0.0, RIVAL_HZ: MIN_MAGNITUDE}
    spectrums = locking_timeline().build() + spectrums_at(
        calling, (3_600.0, 3_600.0 + LOCK_SECONDS)
    )

    samples = track(spectrums)

    assert frequencies(samples)[-2] == CARRIER_HZ
    assert frequencies(samples)[-1] == RIVAL_HZ
