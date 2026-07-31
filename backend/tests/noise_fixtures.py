"""Builders for the estimators and spectrums the noise tests drive.

Spectrums come from ``carrier_fixtures`` — both sub-stages read the same
window off the same readings, so they share one way of writing bins down.
"""

from carrier_fixtures import SETTINGS, spectrum

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import NoiseSample
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    PercentileNoiseEstimator,
)

PERCENTILE = SETTINGS.noise_detector_percentile


def estimator(percentile: float = PERCENTILE) -> PercentileNoiseEstimator:
    return PercentileNoiseEstimator(
        ToneDetectorSettings(noise_detector_percentile=percentile)
    )


def estimate(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    noise_estimator: PercentileNoiseEstimator | None = None,
    batch_size: int | None = None,
) -> tuple[NoiseSample, ...]:
    """Feed ``spectrums`` to one estimator, ``batch_size`` of them per call."""
    reader = noise_estimator or estimator()
    size = batch_size or max(len(spectrums), 1)
    samples: tuple[NoiseSample, ...] = ()
    for offset in range(0, len(spectrums), size):
        reading = SpectrumReading(spectrums=spectrums[offset : offset + size])
        samples += reader.estimate(reading).samples
    return samples


def noises(samples: tuple[NoiseSample, ...]) -> tuple[float, ...]:
    return tuple(sample.noise for sample in samples)


def noise_of(bins: dict[float, float], percentile: float = PERCENTILE) -> float:
    """The floor one estimator reads off a single spectrum of ``bins``."""
    return estimate((spectrum(bins),), noise_estimator=estimator(percentile))[0].noise
