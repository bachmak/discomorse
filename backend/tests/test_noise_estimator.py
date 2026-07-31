import pytest
from carrier_fixtures import MAX_HZ, MIN_HZ, spectrum
from noise_fixtures import estimate, narrow_estimator, noise_of, noises

from morse_decoder.pipeline.dto import NoiseSample

_QUIET = 0.02
_LOUD = 5.0
_FLOOR_BINS = {500.0: _QUIET, 600.0: _QUIET, 800.0: _QUIET, 900.0: _QUIET}
_CARRIER_HZ = 700.0


@pytest.mark.parametrize(
    "bins, want",
    [
        pytest.param({500.0: 0.1, 700.0: 0.2, 900.0: 0.3}, 0.2, id="median-bin"),
        pytest.param({500.0: 0.1, 700.0: 0.2}, 0.15, id="interpolated-between-bins"),
        pytest.param({700.0: 0.4}, 0.4, id="single-bin"),
        pytest.param({500.0: 0.2, 700.0: 0.2}, 0.2, id="flat-floor"),
        pytest.param({500.0: 0.0, 700.0: 0.0}, 0.0, id="silence"),
        pytest.param({500.0: 0.3, 700.0: 0.1, 900.0: 0.2}, 0.2, id="bins-out-of-order"),
        pytest.param({500.0: 0.1, 700.0: 0.1, 900.0: _LOUD}, 0.1, id="carrier-ignored"),
        pytest.param(_FLOOR_BINS | {_CARRIER_HZ: _LOUD}, _QUIET, id="carrier-in-noise"),
    ],
)
def test_estimator_reads_the_floor_off_the_windows_bins(
    bins: dict[float, float], want: float
) -> None:
    assert noise_of(bins) == pytest.approx(want)


@pytest.mark.parametrize(
    "percentile, want",
    [
        pytest.param(0.0, 0.1, id="quietest-bin"),
        pytest.param(25.0, 0.175, id="lower-quartile"),
        pytest.param(50.0, 0.25, id="median-bin"),
        pytest.param(75.0, 0.325, id="upper-quartile"),
        pytest.param(100.0, 0.4, id="loudest-bin"),
    ],
)
def test_estimator_follows_the_configured_percentile(
    percentile: float, want: float
) -> None:
    bins = {500.0: 0.1, 700.0: 0.2, 900.0: 0.3, 1_100.0: 0.4}

    assert noise_of(bins, percentile) == pytest.approx(want)


def test_a_high_enough_percentile_climbs_onto_the_carrier() -> None:
    bins = _FLOOR_BINS | {_CARRIER_HZ: _LOUD}

    assert noise_of(bins, percentile=100.0) == pytest.approx(_LOUD)


@pytest.mark.parametrize(
    "bins, want",
    [
        pytest.param({MIN_HZ: 0.3, 700.0: 0.1}, 0.2, id="lower-edge-included"),
        pytest.param({MAX_HZ: 0.3, 700.0: 0.1}, 0.2, id="upper-edge-included"),
        pytest.param({MIN_HZ - 1: _LOUD, 700.0: 0.1}, 0.1, id="just-below-excluded"),
        pytest.param({MAX_HZ + 1: _LOUD, 700.0: 0.1}, 0.1, id="just-above-excluded"),
        pytest.param({1.0: _LOUD, 700.0: 0.1, 3_000.0: _LOUD}, 0.1, id="far-outside"),
    ],
)
def test_estimator_only_reads_bins_inside_the_window(
    bins: dict[float, float], want: float
) -> None:
    assert noise_of(bins) == pytest.approx(want)


def test_a_narrow_window_ignores_the_bins_just_outside_it() -> None:
    bins = {699.0: _LOUD, _CARRIER_HZ: 0.1, 701.0: _LOUD}

    samples = estimate(
        (spectrum(bins),), noise_estimator=narrow_estimator(699.5, 700.5)
    )

    assert samples == (NoiseSample(noise=0.1),)


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: 1.0, 200.0: 0.5}, id="all-bins-below-window"),
        pytest.param({2_000.0: 1.0, 3_000.0: 0.5}, id="all-bins-above-window"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
def test_estimator_rejects_a_spectrum_that_misses_the_window(
    bins: dict[float, float],
) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        noise_of(bins)


def test_estimator_reports_one_sample_per_spectrum() -> None:
    spectrums = tuple(
        spectrum({700.0: magnitude}, at_second=index * 0.01)
        for index, magnitude in enumerate((0.1, 0.2, 0.3))
    )

    assert estimate(spectrums) == (
        NoiseSample(noise=0.1),
        NoiseSample(noise=0.2),
        NoiseSample(noise=0.3),
    )


def test_a_rising_floor_is_read_as_a_rising_floor() -> None:
    climb = (0.01, 0.02, 0.05, 0.2, 0.5)
    spectrums = tuple(
        spectrum({500.0: level, 900.0: level}, at_second=index * 0.01)
        for index, level in enumerate(climb)
    )

    assert noises(estimate(spectrums)) == pytest.approx(climb)
