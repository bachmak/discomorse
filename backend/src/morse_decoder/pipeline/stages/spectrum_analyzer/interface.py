from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import PcmChunk, SpectrumReading


class SpectrumAnalyzer(ABC):
    @abstractmethod
    async def process(self, chunk: PcmChunk) -> SpectrumReading:
        """Transform one PCM chunk into frequency spectrums."""
        ...
