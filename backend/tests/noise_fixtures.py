"""Builders for the estimators and spectrums the noise tests drive.

Spectrums come from ``carrier_fixtures`` — both stages read the same limited
readings, so they share one way of writing bins down.
"""

from carrier_fixtures import spectrum
from stream_fixtures import stream

from morse_decoder.config import NoiseEstimatorSettings
from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator
from morse_decoder.pipeline.stages.noise_estimator.percentile_noise_estimator import (
    PercentileNoiseEstimator,
)

SETTINGS = NoiseEstimatorSettings()
PERCENTILE = SETTINGS.noise_detector_percentile


def estimator(percentile: float = PERCENTILE) -> PercentileNoiseEstimator:
    return PercentileNoiseEstimator(
        NoiseEstimatorSettings(noise_detector_percentile=percentile)
    )


async def estimate(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    noise_estimator: NoiseEstimator | None = None,
) -> tuple[NoiseSample, ...]:
    """Feed ``spectrums`` to one estimator the way the pipeline would."""
    reader = noise_estimator or estimator()
    return tuple([one async for one in reader.process(stream(*spectrums))])


def noises(samples: tuple[NoiseSample, ...]) -> tuple[float, ...]:
    return tuple(sample.noise for sample in samples)


async def noise_of(bins: dict[float, float], percentile: float = PERCENTILE) -> float:
    """The floor one estimator reads off a single spectrum of ``bins``."""
    read = await estimate((spectrum(bins),), noise_estimator=estimator(percentile))
    return read[0].noise
