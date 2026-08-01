from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.pipeline.dto import CarrierSample, ToneSpectrum


class CarrierSource(ABC):
    """Follows the carrier every spectrum carries, if it has one."""

    @abstractmethod
    def process(
        self, spectrums: AsyncIterable[ToneSpectrum]
    ) -> AsyncIterator[CarrierSample]: ...
