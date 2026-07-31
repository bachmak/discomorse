from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import ToneSpectrum


class SpectrumLimiter(ABC):
    @abstractmethod
    def limit(self, spectrum: ToneSpectrum) -> ToneSpectrum:
        """Cut the spectrum down to the bins worth reading a carrier off."""
        ...
