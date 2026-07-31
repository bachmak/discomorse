from __future__ import annotations

from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    Tone,
)


class CarrierTrackingState(ABC):
    """One state of the carrier tracking machine.

    Every spectrum drives one transition: ``update`` names the state it moves
    the machine into, and that state delivers the carrier out of the same spectrum.
    """

    @abstractmethod
    def update(self, peak: Tone, spectrum: ToneSpectrum) -> CarrierTrackingState: ...

    @abstractmethod
    def get_carrier(self, peak: Tone) -> CarrierSample: ...
