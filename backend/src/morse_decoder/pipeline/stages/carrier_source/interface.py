from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import CarrierSample, ToneSpectrum


class CarrierSource(ABC):
    @abstractmethod
    def track(self, spectrum: ToneSpectrum) -> CarrierSample:
        """Follow the carrier the spectrum carries, if it has one."""
        ...
