import numpy as np

from morse_decoder.config import NoiseEstimatorSettings
from morse_decoder.pipeline.dto import FrequencyWindow, NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator


class PercentileNoiseEstimator(NoiseEstimator):
    """Takes the noise floor of a spectrum as a percentile of its bins."""

    def __init__(self, settings: NoiseEstimatorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._percentile = settings.noise_detector_percentile

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        windowed = self._window.limit(spectrum)
        magnitudes = [tone.magnitude for tone in windowed.magnitudes]
        return NoiseSample(noise=float(np.percentile(magnitudes, self._percentile)))
