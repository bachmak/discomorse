from __future__ import annotations

from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    SpectrumPeak,
)


class CarrierTrackingState(ABC):
    """One state of the carrier tracking machine.

    Every spectrum drives one transition: ``update`` names the state it moves
    the machine into, and that state ``read``s the carrier out of the very same
    spectrum. So a sample already speaks for the state the next spectrum meets.
    """

    @abstractmethod
    def update(self, peak: SpectrumPeak) -> CarrierTrackingState:
        """The state this spectrum moves the machine into."""
        ...

    @abstractmethod
    def read(self, peak: SpectrumPeak) -> CarrierSample:
        """The carrier this state reads out of the spectrum."""
        ...
