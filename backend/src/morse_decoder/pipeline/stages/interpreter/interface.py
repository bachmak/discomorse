from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import MorseElement, Transcription


class Interpreter(ABC):
    @abstractmethod
    def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Transcription]:
        """Render a stream of decoded elements into corrected, readable text."""
        ...
