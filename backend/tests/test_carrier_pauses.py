"""Regression tests for what a locked carrier reports while the key is up."""

import datetime

import pytest
from audio_fixtures import EPOCH
from carrier_fixtures import track

from morse_decoder.pipeline.dto import CarrierSample, ToneMagnitude, ToneSpectrum

_CARRIER_HZ = 700.0
_RIVAL_HZ = 1_100.0
_LOUD = 0.9
_STEP_S = 0.002
_SIGHTINGS_TO_LOCK = 30


def _spectrum(bins: dict[float, float], at_second: float) -> ToneSpectrum:
    return ToneSpectrum(
        ts=EPOCH + datetime.timedelta(seconds=at_second),
        magnitudes=tuple(
            ToneMagnitude(frequency=frequency, magnitude=magnitude)
            for frequency, magnitude in bins.items()
        ),
    )


def _keyed(levels: tuple[float, ...]) -> tuple[ToneSpectrum, ...]:
    """One spectrum per level, the carrier at that level and a silent rival bin."""
    return tuple(
        _spectrum({_CARRIER_HZ: level, _RIVAL_HZ: 0.0}, index * _STEP_S)
        for index, level in enumerate(levels)
    )


async def _track(spectrums: tuple[ToneSpectrum, ...]) -> tuple[CarrierSample, ...]:
    return await track(spectrums)


@pytest.mark.parametrize(
    "tail, want_magnitude",
    [
        pytest.param(0.0, 0.0, id="key-up-is-silent"),
        pytest.param(0.3, 0.3, id="carrier-fades-but-keeps-transmitting"),
        pytest.param(_LOUD, _LOUD, id="carrier-holds-its-level"),
    ],
)
async def test_locked_carrier_reports_the_current_level(
    tail: float, want_magnitude: float
) -> None:
    samples = await _track(_keyed((_LOUD,) * _SIGHTINGS_TO_LOCK + (tail,)))

    assert samples[-1].is_locked
    assert samples[-1].tone.magnitude == pytest.approx(want_magnitude)


async def test_locked_carrier_stamps_every_sample_with_its_own_spectrum_time() -> None:
    spectrums = _keyed((_LOUD,) * _SIGHTINGS_TO_LOCK + (0.0,) * 100)

    samples = await _track(spectrums)

    assert [sample.tone.ts for sample in samples] == [
        spectrum.ts for spectrum in spectrums
    ]


async def test_a_pause_is_visible_in_what_the_source_reports() -> None:
    """Key-down and key-up must not produce identical samples."""
    spectrums = _keyed((_LOUD,) * _SIGHTINGS_TO_LOCK + (0.0,) * 50 + (_LOUD,) * 50)

    samples = await _track(spectrums)

    keyed_down = samples[_SIGHTINGS_TO_LOCK - 1]
    keyed_up = samples[_SIGHTINGS_TO_LOCK + 25]
    assert keyed_up.tone.magnitude < keyed_down.tone.magnitude
