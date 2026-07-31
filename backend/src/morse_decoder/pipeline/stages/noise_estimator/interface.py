from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum


class NoiseEstimator(ABC):
    @abstractmethod
    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        """Read the noise floor the spectrum sits on."""
        ...
