from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import TimingReading, ToneReading


class TimingDecoder(ABC):
    @abstractmethod
    async def process(self, reading: ToneReading) -> TimingReading:
        """Decode the reading's tone samples into morse timing elements."""
        ...
