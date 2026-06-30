from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import (
    PcmChunk,
    SpectrumReading,
    TimingReading,
    ToneReading,
    Transcription,
)


class SpectrumAnalyzer(ABC):
    @abstractmethod
    async def process(self, chunk: PcmChunk) -> SpectrumReading:
        """Transform one PCM chunk into frequency spectrums."""
        ...


class ToneDetector(ABC):
    @abstractmethod
    async def process(self, reading: SpectrumReading) -> ToneReading:
        """Detect tone on/off samples from the spectrums."""
        ...


class TimingDecoder(ABC):
    @abstractmethod
    async def process(self, reading: ToneReading) -> TimingReading:
        """Decode the reading's tone samples into morse timing elements."""
        ...


class Interpreter(ABC):
    @abstractmethod
    async def interpret(self, reading: TimingReading) -> Transcription:
        """Render decoded elements into corrected, readable text."""
        ...
