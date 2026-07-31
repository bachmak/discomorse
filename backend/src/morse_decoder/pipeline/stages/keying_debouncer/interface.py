import datetime
from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import KeyingSample


class KeyingDebouncer(ABC):
    @abstractmethod
    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample:
        """Report the side of the key that has held long enough to be believed."""
        ...
