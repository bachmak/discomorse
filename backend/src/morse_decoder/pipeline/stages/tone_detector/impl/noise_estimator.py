from abc import ABC, abstractmethod

import numpy as np

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import NoiseSample


class NoiseEstimator(ABC):
    @abstractmethod
    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample: ...


class PercentileNoiseEstimator(NoiseEstimator):
    """Takes the noise floor of a spectrum as a percentile of its bins."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._percentile = settings.noise_detector_percentile

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        magnitudes = [tone.magnitude for tone in spectrum.magnitudes]
        return NoiseSample(noise=float(np.percentile(magnitudes, self._percentile)))
