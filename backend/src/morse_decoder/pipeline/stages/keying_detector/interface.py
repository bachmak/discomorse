from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import CarrierSample, KeyingSample, NoiseSample


class KeyingDetector(ABC):
    @abstractmethod
    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample:
        """Tell whether the carrier stands above the noise as a keyed tone."""
        ...
