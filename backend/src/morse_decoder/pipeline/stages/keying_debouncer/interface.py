from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import ToneSample


class KeyingDebouncer(ABC):
    """Reports the side of the key that has held long enough to be believed."""

    @abstractmethod
    def process(
        self, samples: AsyncIterable[ToneSample]
    ) -> AsyncIterator[ToneSample]: ...
