from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import SpectrumReading, ToneReading


class ToneDetector(ABC):
    @abstractmethod
    async def process(self, reading: SpectrumReading) -> ToneReading:
        """Detect tone on/off samples from the spectrums."""
        ...
