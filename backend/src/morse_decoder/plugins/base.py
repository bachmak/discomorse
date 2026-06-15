from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import (
    PcmChunk,
    TimingReading,
    ToneReading,
    Transcription,
)


class ToneDetector(ABC):
    @abstractmethod
    async def process(self, chunk: PcmChunk) -> ToneReading:
        """Analyze one PCM chunk into a tone reading."""
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
