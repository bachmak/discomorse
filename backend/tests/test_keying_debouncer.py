"""What the debouncer lets through, and how long it makes a change wait."""

import pytest
from debounce_fixtures import (
    BETWEEN_DELAYS_SECONDS,
    FALL_SECONDS,
    RISE_SECONDS,
    SETTLE_SECONDS,
    STEP_S,
    KeyReading,
    KeyTimeline,
    blip,
    debounced,
    debouncer,
    edges,
    keyed_seconds,
)

from morse_decoder.config import ToneDetectorSettings

_DIT_SECONDS = 1.2 / 20  # a dit at the speed the timing stage is seeded with
_FLAP_CYCLES = 20


@pytest.mark.parametrize(
    "is_on, want_edges",
    [
        pytest.param(False, 0, id="a-line-resting-up"),
        pytest.param(True, 1, id="a-line-keyed-down-from-the-start"),
    ],
)
def test_a_key_that_never_changes_settles_on_its_side_and_stays_there(
    is_on: bool, want_edges: int
) -> None:
    flags = debounced(KeyTimeline().hold(is_on, SETTLE_SECONDS).build())

    assert flags[0] is False
    assert flags[-1] is is_on
    assert edges(flags) == want_edges


@pytest.mark.parametrize(
    "seconds, want",
    [
        pytest.param(RISE_SECONDS / 2, 0, id="shorter-than-the-rise-delay"),
        pytest.param(RISE_SECONDS * 2, 2, id="longer-than-the-rise-delay"),
    ],
)
def test_the_key_falls_only_once_it_has_been_held_down_past_the_rise_delay(
    seconds: float, want: int
) -> None:
    assert edges(debounced(blip(True, seconds))) == want


@pytest.mark.parametrize(
    "seconds, want",
    [
        pytest.param(FALL_SECONDS / 2, 1, id="shorter-than-the-fall-delay"),
        pytest.param(FALL_SECONDS * 2, 3, id="longer-than-the-fall-delay"),
    ],
)
def test_the_key_lifts_only_once_it_has_been_let_up_past_the_fall_delay(
    seconds: float, want: int
) -> None:
    assert edges(debounced(blip(False, seconds))) == want


def test_the_key_waits_longer_to_lift_than_it_waits_to_fall() -> None:
    """One stretch, read on both sides: long enough to key, too short to lift."""
    assert edges(debounced(blip(True, BETWEEN_DELAYS_SECONDS))) == 2
    assert edges(debounced(blip(False, BETWEEN_DELAYS_SECONDS))) == 1


@pytest.mark.parametrize(
    "step_seconds, want",
    [
        pytest.param(RISE_SECONDS / 4, 0, id="readings-too-close-to-fill-the-delay"),
        pytest.param(RISE_SECONDS, 2, id="readings-far-enough-apart"),
    ],
)
def test_a_delay_is_a_stretch_of_time_and_not_a_count_of_readings(
    step_seconds: float, want: int
) -> None:
    line = (
        KeyTimeline(step_seconds)
        .hold(False, SETTLE_SECONDS)
        .add(True, count=2)
        .hold(False, SETTLE_SECONDS)
        .build()
    )

    assert edges(debounced(line)) == want


def test_a_key_flapping_faster_than_the_delays_never_reaches_the_output() -> None:
    line = (
        KeyTimeline()
        .hold(False, SETTLE_SECONDS)
        .alternate(_FLAP_CYCLES)
        .hold(False, SETTLE_SECONDS)
        .build()
    )

    assert not any(debounced(line))


def test_a_mark_torn_by_a_dropout_still_reads_as_one_mark() -> None:
    line = (
        KeyTimeline()
        .hold(False, SETTLE_SECONDS)
        .hold(True, _DIT_SECONDS)
        .hold(False, FALL_SECONDS / 2)
        .hold(True, _DIT_SECONDS)
        .hold(False, SETTLE_SECONDS)
        .build()
    )

    assert edges(debounced(line)) == 2


def test_the_gap_between_two_elements_lives_through_the_debouncer() -> None:
    line = (
        KeyTimeline()
        .hold(False, SETTLE_SECONDS)
        .hold(True, _DIT_SECONDS)
        .hold(False, _DIT_SECONDS)
        .hold(True, _DIT_SECONDS)
        .hold(False, SETTLE_SECONDS)
        .build()
    )

    assert edges(debounced(line)) == 4


def test_a_mark_comes_out_stretched_by_the_gap_between_the_two_delays() -> None:
    """Both edges arrive late, and the key falls sooner than it lifts."""
    line = (
        KeyTimeline()
        .hold(False, SETTLE_SECONDS)
        .hold(True, _DIT_SECONDS)
        .hold(False, SETTLE_SECONDS)
        .build()
    )

    assert keyed_seconds(line) == pytest.approx(
        _DIT_SECONDS + FALL_SECONDS - RISE_SECONDS, abs=STEP_S
    )


def test_a_debouncer_without_delays_passes_every_change_straight_through() -> None:
    line = KeyTimeline().alternate(_FLAP_CYCLES).build()
    reader = debouncer(
        ToneDetectorSettings(debounce_rise_seconds=0.0, debounce_fall_seconds=0.0)
    )

    assert debounced(line, keying_debouncer=reader) == tuple(
        one.sample.is_on for one in line
    )


def test_a_stream_read_in_two_parts_reads_as_one_stream() -> None:
    """The split falls inside a change the debouncer has begun but not passed on."""
    readings = blip(True, RISE_SECONDS * 2)
    split = len(readings) // 2
    reader = debouncer()

    head = debounced(readings[:split], keying_debouncer=reader)
    tail = debounced(readings[split:], keying_debouncer=reader)

    assert head + tail == debounced(readings)


@pytest.mark.parametrize(
    "readings",
    [
        pytest.param(blip(True, RISE_SECONDS * 2), id="a-key-that-falls"),
        pytest.param(blip(False, FALL_SECONDS * 2), id="a-key-that-lifts"),
        pytest.param(
            KeyTimeline().alternate(_FLAP_CYCLES).build(), id="a-flapping-key"
        ),
    ],
)
def test_every_reading_yields_exactly_one_sample(
    readings: tuple[KeyReading, ...],
) -> None:
    assert len(debounced(readings)) == len(readings)
