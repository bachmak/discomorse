from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from morse_decoder.pipeline.dto import PcmChunk


class AudioSource(ABC):
    @abstractmethod
    def stream(self) -> AsyncIterator[PcmChunk]:
        """Yield raw Int16 PCM chunks at the configured sample rate."""
        ...
