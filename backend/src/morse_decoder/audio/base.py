from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AudioSource(ABC):
    @abstractmethod
    def stream(self) -> AsyncIterator[bytes]:
        """Yield raw Int16 PCM chunks at the configured sample rate."""
        ...
