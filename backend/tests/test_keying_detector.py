"""Where the key falls and where it lifts, given a carrier over a noise floor."""

import pytest
from keying_fixtures import (
    FLOOR,
    IN_BAND,
    OFF_FACTOR,
    ON_FACTOR,
    OVER_ON,
    UNDER_OFF,
    Step,
    detector,
    keyed,
    steps,
    steps_over,
    unlocked,
)

_AT_ON = FLOOR * ON_FACTOR
_AT_OFF = FLOOR * OFF_FACTOR
_LOUD_FLOOR = FLOOR * 10
_SETTLE = 20


def _keyed_pattern(magnitudes: tuple[float, ...]) -> tuple[bool, ...]:
    return keyed(steps(magnitudes))


@pytest.mark.parametrize(
    "magnitudes, want",
    [
        pytest.param((UNDER_OFF,), (False,), id="a-carrier-in-the-mud"),
        pytest.param((IN_BAND,), (False,), id="a-carrier-inside-the-band"),
        pytest.param((_AT_ON,), (False,), id="a-carrier-exactly-on-the-bar"),
        pytest.param((OVER_ON,), (True,), id="a-carrier-over-the-bar"),
    ],
)
def test_the_key_falls_only_once_the_carrier_clears_the_upper_threshold(
    magnitudes: tuple[float, ...], want: tuple[bool, ...]
) -> None:
    assert _keyed_pattern(magnitudes) == want


@pytest.mark.parametrize(
    "magnitudes, want",
    [
        pytest.param((OVER_ON, IN_BAND), (True, True), id="held-inside-the-band"),
        pytest.param((OVER_ON, _AT_OFF), (True, True), id="held-on-the-lower-bar"),
        pytest.param((OVER_ON, UNDER_OFF), (True, False), id="lifted-under-the-band"),
        pytest.param(
            (OVER_ON, IN_BAND, IN_BAND, UNDER_OFF, IN_BAND),
            (True, True, True, False, False),
            id="the-band-belongs-to-whichever-side-the-key-is-on",
        ),
    ],
)
def test_the_key_lifts_only_once_the_carrier_sinks_under_the_lower_threshold(
    magnitudes: tuple[float, ...], want: tuple[bool, ...]
) -> None:
    assert _keyed_pattern(magnitudes) == want


def test_a_keyed_carrier_is_read_as_the_pattern_it_was_keyed_in() -> None:
    magnitudes = (OVER_ON,) * 2 + (UNDER_OFF,) * 3 + (OVER_ON,) * 2

    assert _keyed_pattern(magnitudes) == (True, True, False, False, False, True, True)


@pytest.mark.parametrize(
    "magnitudes",
    [
        pytest.param((OVER_ON,) * 3, id="a-carrier-over-the-bar"),
        pytest.param((OVER_ON * 100,) * 3, id="a-carrier-far-over-the-bar"),
    ],
)
def test_a_carrier_the_source_never_locked_never_keys_the_line(
    magnitudes: tuple[float, ...],
) -> None:
    assert not any(keyed(unlocked(steps(magnitudes))))


def test_losing_the_lock_lifts_a_key_that_was_down() -> None:
    down = steps((OVER_ON,))

    assert keyed(down + unlocked(down) + down) == (True, False, True)


def test_the_thresholds_keep_following_the_noise_while_the_lock_is_gone() -> None:
    """A floor that climbed unheard still has to be cleared once the lock returns."""
    gap = unlocked(steps((OVER_ON,) * _SETTLE, floor=_LOUD_FLOOR))
    quiet_gap = unlocked(steps((OVER_ON,) * _SETTLE))

    assert keyed(gap + steps((OVER_ON,))) == (False,) * _SETTLE + (False,)
    assert keyed(quiet_gap + steps((OVER_ON,))) == (False,) * _SETTLE + (True,)


def test_a_floor_rising_over_a_steady_carrier_lifts_the_key_and_keeps_it_up() -> None:
    climb = tuple(FLOOR * (1 + index) for index in range(_SETTLE))

    flags = keyed(steps_over(OVER_ON, climb))

    assert flags[0]
    assert not flags[-1]
    assert sorted(flags, reverse=True) == list(flags)


def test_a_stream_read_in_two_parts_reads_as_one_stream() -> None:
    readings = steps((OVER_ON, IN_BAND, UNDER_OFF, IN_BAND, OVER_ON))
    reader = detector()

    head = keyed(readings[:2], keying_detector=reader)
    tail = keyed(readings[2:], keying_detector=reader)

    assert head + tail == keyed(readings)


@pytest.mark.parametrize(
    "readings",
    [
        pytest.param(steps((OVER_ON, UNDER_OFF, IN_BAND)), id="a-keyed-carrier"),
        pytest.param(unlocked(steps((OVER_ON,) * 3)), id="a-carrier-never-locked"),
        pytest.param(steps_over(OVER_ON, (FLOOR, _LOUD_FLOOR, FLOOR)), id="in-noise"),
    ],
)
def test_every_reading_yields_exactly_one_sample(readings: tuple[Step, ...]) -> None:
    assert len(keyed(readings)) == len(readings)
