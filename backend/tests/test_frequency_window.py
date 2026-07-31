"""What the tone detector lets through to its substages, and what it cuts away."""

import pytest
from carrier_fixtures import MAX_HZ, MIN_HZ, WINDOW, spectrum

from morse_decoder.pipeline.stages.tone_detector.impl.dto import FrequencyWindow
from morse_decoder.pipeline.stages.tone_detector.impl.helpers import limit_to_window

_LOUD = 1.0


@pytest.mark.parametrize(
    "bins, want_frequencies",
    [
        pytest.param({700.0: _LOUD}, (700.0,), id="inside"),
        pytest.param({MIN_HZ: _LOUD}, (MIN_HZ,), id="lower-edge-included"),
        pytest.param({MAX_HZ: _LOUD}, (MAX_HZ,), id="upper-edge-included"),
        pytest.param({MIN_HZ - 1: _LOUD, 700.0: _LOUD}, (700.0,), id="just-below-cut"),
        pytest.param({MAX_HZ + 1: _LOUD, 700.0: _LOUD}, (700.0,), id="just-above-cut"),
        pytest.param(
            {1.0: _LOUD, 700.0: _LOUD, 3_000.0: _LOUD}, (700.0,), id="far-outside-cut"
        ),
    ],
)
def test_the_window_keeps_only_the_bins_it_covers(
    bins: dict[float, float], want_frequencies: tuple[float, ...]
) -> None:
    limited = limit_to_window(spectrum(bins), WINDOW)

    assert tuple(tone.frequency for tone in limited.magnitudes) == want_frequencies


def test_the_window_stamps_the_limited_spectrum_with_its_own_time() -> None:
    one = spectrum({700.0: _LOUD}, at_second=0.5)

    assert limit_to_window(one, WINDOW).ts == one.ts


def test_a_narrow_window_cuts_the_bins_just_outside_it() -> None:
    narrow = FrequencyWindow(699.5, 700.5)
    bins = {699.0: _LOUD, 700.0: 0.1, 701.0: _LOUD}

    limited = limit_to_window(spectrum(bins), narrow)

    assert tuple(tone.frequency for tone in limited.magnitudes) == (700.0,)


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: _LOUD, 200.0: 0.5}, id="all-bins-below-window"),
        pytest.param({2_000.0: _LOUD, 3_000.0: 0.5}, id="all-bins-above-window"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
def test_a_spectrum_missing_the_window_is_rejected(bins: dict[float, float]) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        limit_to_window(spectrum(bins), WINDOW)
