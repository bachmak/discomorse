"""The band the thresholds hold over a noise floor that moves under them."""

import pytest
from keying_fixtures import FLOOR, OFF_FACTOR, ON_FACTOR, offs, ons, track, tracker

from morse_decoder.config import ToneDetectorSettings

_FAST = ToneDetectorSettings(threshold_rise_alpha=0.5, threshold_fall_alpha=0.1)
_INSTANT = ToneDetectorSettings(threshold_rise_alpha=1.0, threshold_fall_alpha=1.0)
_LOUD_FLOOR = FLOOR * 10
_RUN = 100
_SETTLED = 0.1

_STREAMS = {
    "a-single-floor": (FLOOR,),
    "a-steady-floor": (FLOOR,) * 5,
    "a-rising-floor": (FLOOR, FLOOR * 2, FLOOR * 5, _LOUD_FLOOR),
    "a-fading-floor": (_LOUD_FLOOR, FLOOR * 5, FLOOR * 2, FLOOR),
    "a-burst-of-noise": (FLOOR, FLOOR, _LOUD_FLOOR, _LOUD_FLOOR, FLOOR, FLOOR),
    "keying-in-noise": (FLOOR, _LOUD_FLOOR) * 4,
    "silence": (0.0,) * 5,
}
_TRACKED = [pytest.param(floors, id=name) for name, floors in _STREAMS.items()]


def _floors_read_back(
    floors: tuple[float, ...], settings: ToneDetectorSettings = _FAST
) -> tuple[float, ...]:
    """The level the tracker holds, read back off the threshold it puts over it."""
    bands = track(floors, threshold_tracker=tracker(settings))
    return tuple(threshold / ON_FACTOR for threshold in ons(bands))


def _steps_to_settle(floors: tuple[float, ...], target: float) -> int:
    """How many readings before the level comes within a tenth of ``target``."""
    levels = _floors_read_back(floors, ToneDetectorSettings())
    return next(
        (
            index
            for index, level in enumerate(levels)
            if abs(level - target) <= target * _SETTLED
        ),
        len(levels),
    )


@pytest.mark.parametrize(
    "floors, want",
    [
        pytest.param((0.1,), (0.1,), id="the-first-floor-seeds-the-level"),
        pytest.param((0.1, 0.1, 0.1), (0.1, 0.1, 0.1), id="a-steady-floor-holds"),
        pytest.param((0.1, 0.3), (0.1, 0.2), id="half-way-up-in-one-step"),
        pytest.param((0.1, 0.3, 0.3), (0.1, 0.2, 0.25), id="climbing-in-halves"),
        pytest.param((0.1, 0.0), (0.1, 0.09), id="a-tenth-of-the-way-down"),
        pytest.param((0.1, 0.0, 0.0), (0.1, 0.09, 0.081), id="sinking-in-tenths"),
        pytest.param((0.1, 0.3, 0.1), (0.1, 0.2, 0.19), id="up-fast-then-down-slow"),
    ],
)
def test_the_floor_is_followed_at_the_rate_its_direction_names(
    floors: tuple[float, ...], want: tuple[float, ...]
) -> None:
    assert _floors_read_back(floors) == pytest.approx(want)


@pytest.mark.parametrize(
    "on_factor, off_factor",
    [
        pytest.param(ON_FACTOR, OFF_FACTOR, id="the-configured-factors"),
        pytest.param(10.0, 1.5, id="a-high-bar-to-key-down"),
        pytest.param(1.2, 1.1, id="a-narrow-band"),
    ],
)
def test_both_thresholds_are_the_named_multiples_of_the_same_floor(
    on_factor: float, off_factor: float
) -> None:
    settings = ToneDetectorSettings(
        threshold_on_factor=on_factor, threshold_off_factor=off_factor
    )

    bands = track((FLOOR,), threshold_tracker=tracker(settings))

    assert ons(bands) == pytest.approx((FLOOR * on_factor,))
    assert offs(bands) == pytest.approx((FLOOR * off_factor,))


@pytest.mark.parametrize("floors", _TRACKED)
def test_the_lower_threshold_always_leaves_room_under_the_upper_one(
    floors: tuple[float, ...],
) -> None:
    for band in track(floors):
        assert band.off <= band.on


@pytest.mark.parametrize("floors", _TRACKED)
def test_the_thresholds_never_leave_the_range_the_floors_span(
    floors: tuple[float, ...],
) -> None:
    for band in track(floors):
        assert min(floors) * ON_FACTOR <= band.on <= max(floors) * ON_FACTOR


@pytest.mark.parametrize("floors", _TRACKED)
def test_a_stream_read_in_two_parts_reads_as_one_stream(
    floors: tuple[float, ...],
) -> None:
    reader = tracker()

    head = track(floors[:2], threshold_tracker=reader)
    tail = track(floors[2:], threshold_tracker=reader)

    assert head + tail == track(floors)


@pytest.mark.parametrize("floors", _TRACKED)
def test_a_tracker_that_never_smooths_repeats_the_floor_it_is_given(
    floors: tuple[float, ...],
) -> None:
    assert _floors_read_back(floors, _INSTANT) == pytest.approx(floors)


@pytest.mark.parametrize("gain", [0.5, 2.0, 100.0])
def test_scaling_every_floor_scales_both_thresholds_with_it(gain: float) -> None:
    floors = _STREAMS["a-burst-of-noise"]

    scaled = track(tuple(floor * gain for floor in floors))

    assert ons(scaled) == pytest.approx([level * gain for level in ons(track(floors))])
    assert offs(scaled) == pytest.approx(
        [level * gain for level in offs(track(floors))]
    )


def test_a_floor_that_never_rises_leaves_the_thresholds_on_the_ground() -> None:
    bands = track(_STREAMS["silence"])

    assert ons(bands) == pytest.approx([0.0] * len(bands))
    assert offs(bands) == pytest.approx([0.0] * len(bands))


def test_the_floor_climbs_to_a_burst_in_fewer_readings_than_it_sinks_back() -> None:
    climbing = (FLOOR,) + (_LOUD_FLOOR,) * _RUN
    sinking = (_LOUD_FLOOR,) + (FLOOR,) * _RUN

    assert _steps_to_settle(climbing, _LOUD_FLOOR) < _steps_to_settle(sinking, FLOOR)


def test_a_burst_of_noise_leaves_the_thresholds_over_where_it_found_them() -> None:
    """The lull after a burst is not believed at once: the bar stays raised."""
    levels = _floors_read_back(_STREAMS["a-burst-of-noise"], ToneDetectorSettings())

    assert levels[-1] > levels[0]
    assert levels[-1] < _LOUD_FLOOR
