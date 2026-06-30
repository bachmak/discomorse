from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import TimingReading, Transcription


class Interpreter(ABC):
    @abstractmethod
    async def interpret(self, reading: TimingReading) -> Transcription:
        """Render decoded elements into corrected, readable text."""
        ...
