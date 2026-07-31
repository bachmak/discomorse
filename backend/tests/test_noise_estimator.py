import pytest
from carrier_fixtures import spectrum
from noise_fixtures import estimate, noise_of, noises

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
async def test_estimator_reads_the_floor_off_the_bins_it_is_given(
    bins: dict[float, float], want: float
) -> None:
    assert await noise_of(bins) == pytest.approx(want)


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
async def test_estimator_follows_the_configured_percentile(
    percentile: float, want: float
) -> None:
    bins = {500.0: 0.1, 700.0: 0.2, 900.0: 0.3, 1_100.0: 0.4}

    assert await noise_of(bins, percentile) == pytest.approx(want)


async def test_a_high_enough_percentile_climbs_onto_the_carrier() -> None:
    bins = _FLOOR_BINS | {_CARRIER_HZ: _LOUD}

    assert await noise_of(bins, percentile=100.0) == pytest.approx(_LOUD)


async def test_estimator_reports_one_sample_per_spectrum() -> None:
    spectrums = tuple(
        spectrum({700.0: magnitude}, at_second=index * 0.01)
        for index, magnitude in enumerate((0.1, 0.2, 0.3))
    )

    assert await estimate(spectrums) == (
        NoiseSample(noise=0.1),
        NoiseSample(noise=0.2),
        NoiseSample(noise=0.3),
    )


async def test_a_rising_floor_is_read_as_a_rising_floor() -> None:
    climb = (0.01, 0.02, 0.05, 0.2, 0.5)
    spectrums = tuple(
        spectrum({500.0: level, 900.0: level}, at_second=index * 0.01)
        for index, level in enumerate(climb)
    )

    assert noises(await estimate(spectrums)) == pytest.approx(climb)
