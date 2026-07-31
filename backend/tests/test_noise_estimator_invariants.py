"""Properties that must hold for every stream the estimator is given."""

import pytest
from carrier_fixtures import (
    CARRIER_HZ,
    KEYED,
    LOCK_SECONDS,
    LOUD,
    RIVAL_HZ,
    SILENT,
    SpectrumTimeline,
)
from noise_fixtures import estimate, estimator, noise_of, noises

from morse_decoder.pipeline.dto import ToneSpectrum

_QUIET = 0.02
_NOISY = {CARRIER_HZ: LOUD, RIVAL_HZ: _QUIET, 500.0: _QUIET / 2, 900.0: _QUIET * 3}
_PERCENTILES = (0.0, 10.0, 50.0, 90.0, 100.0)

_SCENARIOS = {
    "a-keyed-carrier": SpectrumTimeline().hold(KEYED, LOCK_SECONDS * 4).build(),
    "silence": SpectrumTimeline().hold(SILENT, LOCK_SECONDS * 4).build(),
    "keying-in-noise": SpectrumTimeline()
    .alternate(_NOISY, _NOISY | {CARRIER_HZ: 0.0}, cycles=4, run=2)
    .build(),
    "a-single-spectrum": SpectrumTimeline().add(_NOISY).build(),
}
_STREAMS = [pytest.param(spectrums, id=name) for name, spectrums in _SCENARIOS.items()]


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_every_spectrum_yields_exactly_one_sample(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    assert len(estimate(spectrums)) == len(spectrums)


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_the_same_stream_reports_the_same_samples_every_time(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    assert estimate(spectrums) == estimate(spectrums)


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_one_estimator_reads_a_stream_as_a_fresh_one_would(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    """The estimator carries no state: a used one still reads the head the same."""
    used = estimator()
    estimate(spectrums, noise_estimator=used)

    assert estimate(spectrums, noise_estimator=used) == estimate(spectrums)


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_the_floor_never_leaves_the_range_of_the_spectrums_bins(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    for one, noise in zip(spectrums, noises(estimate(spectrums)), strict=True):
        levels = [tone.magnitude for tone in one.magnitudes]
        assert min(levels) <= noise <= max(levels)


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_a_higher_percentile_never_reads_a_lower_floor(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    floors = [
        noises(estimate(spectrums, noise_estimator=estimator(percentile)))
        for percentile in _PERCENTILES
    ]

    for lower, higher in zip(floors, floors[1:], strict=False):
        assert all(a <= b for a, b in zip(lower, higher, strict=True))


@pytest.mark.parametrize("gain", [0.5, 2.0, 100.0])
def test_scaling_every_bin_scales_the_floor_with_it(gain: float) -> None:
    bins = {500.0: 0.01, 700.0: 0.3, 900.0: LOUD}

    scaled = {frequency: level * gain for frequency, level in bins.items()}

    assert noise_of(scaled) == pytest.approx(noise_of(bins) * gain)


def test_a_stream_read_in_two_parts_reads_as_one_stream() -> None:
    spectrums = _SCENARIOS["keying-in-noise"]
    reader = estimator()

    head = estimate(spectrums[:3], noise_estimator=reader)
    tail = estimate(spectrums[3:], noise_estimator=reader)

    assert head + tail == estimate(spectrums)
