from abc import ABC, abstractmethod

import numpy as np

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    FrequencyWindow,
    NoiseReading,
    NoiseSample,
)
from morse_decoder.pipeline.stages.tone_detector.impl.helpers import tones_in_window


class NoiseEstimator(ABC):
    @abstractmethod
    def estimate(self, reading: SpectrumReading) -> NoiseReading: ...


class PercentileNoiseEstimator(NoiseEstimator):
    """Takes the noise floor of a spectrum as a percentile of its window's bins."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._percentile = settings.noise_detector_percentile

    def estimate(self, reading: SpectrumReading) -> NoiseReading:
        return NoiseReading(
            samples=tuple(self._sample(spectrum) for spectrum in reading.spectrums)
        )

    def _sample(self, spectrum: ToneSpectrum) -> NoiseSample:
        tones = tones_in_window(spectrum, self._window)
        magnitudes = [tone.magnitude for tone in tones]
        return NoiseSample(noise=float(np.percentile(magnitudes, self._percentile)))
