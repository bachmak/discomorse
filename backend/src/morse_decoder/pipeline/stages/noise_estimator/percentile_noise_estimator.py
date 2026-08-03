import numpy as np

from morse_decoder.config import NoiseEstimatorSettings
from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator


class PercentileNoiseEstimator(NoiseEstimator):
    """Takes the noise floor of a spectrum as a percentile of its bins."""

    def __init__(self, settings: NoiseEstimatorSettings) -> None:
        self._percentile = settings.noise_detector_percentile

    def process_single(self, spectrum: ToneSpectrum) -> NoiseSample:
        magnitudes = [tone.magnitude for tone in spectrum.magnitudes]
        return NoiseSample(noise=float(np.percentile(magnitudes, self._percentile)))
