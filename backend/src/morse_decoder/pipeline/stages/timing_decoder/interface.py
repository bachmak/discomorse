from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import MorseElement, ToneSample


class TimingDecoder(ABC):
    @abstractmethod
    def process(
        self, samples: AsyncIterable[ToneSample]
    ) -> AsyncIterator[MorseElement]:
        """Decode a stream of tone samples into morse timing elements."""
        ...
