from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import PcmChunk, ToneSpectrum


class SpectrumAnalyzer(ABC):
    @abstractmethod
    def process(self, chunks: AsyncIterable[PcmChunk]) -> AsyncIterator[ToneSpectrum]:
        """Turn a stream of PCM chunks into a stream of frequency spectrums."""
        ...
