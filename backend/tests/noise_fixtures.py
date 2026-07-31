"""Builders for the estimators and spectrums the noise tests drive.

Spectrums come from ``carrier_fixtures`` — both stages read the same window off
the same readings, so they share one way of writing bins down.
"""

from carrier_fixtures import spectrum

from morse_decoder.config import NoiseEstimatorSettings
from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.noise_estimator.percentile_noise_estimator import (
    PercentileNoiseEstimator,
)

SETTINGS = NoiseEstimatorSettings()
PERCENTILE = SETTINGS.noise_detector_percentile


def estimator(percentile: float = PERCENTILE) -> PercentileNoiseEstimator:
    return PercentileNoiseEstimator(
        NoiseEstimatorSettings(noise_detector_percentile=percentile)
    )


def narrow_estimator(min_hz: float, max_hz: float) -> PercentileNoiseEstimator:
    """An estimator that reads a window of its own instead of the default one."""
    return PercentileNoiseEstimator(
        NoiseEstimatorSettings(carrier_min_hz=min_hz, carrier_max_hz=max_hz)
    )


def estimate(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    noise_estimator: PercentileNoiseEstimator | None = None,
) -> tuple[NoiseSample, ...]:
    """Feed ``spectrums`` to one estimator the way the pipeline would."""
    reader = noise_estimator or estimator()
    return tuple(reader.estimate(spectrum) for spectrum in spectrums)


def noises(samples: tuple[NoiseSample, ...]) -> tuple[float, ...]:
    return tuple(sample.noise for sample in samples)


def noise_of(bins: dict[float, float], percentile: float = PERCENTILE) -> float:
    """The floor one estimator reads off a single spectrum of ``bins``."""
    return estimate((spectrum(bins),), noise_estimator=estimator(percentile))[0].noise
