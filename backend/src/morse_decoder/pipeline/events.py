from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.api.wire import (
    FFTMessage,
    MorseMessage,
    OscilloscopeMessage,
    ServerMessage,
    TextMessage,
    WaterfallMessage,
)
from morse_decoder.pipeline.dto import MorseElement, ToneSample, ToneSpectrum


class OutboundEvent(ABC):
    """Base for everything the pipeline emits toward the client."""

    @abstractmethod
    def to_message(self) -> ServerMessage:
        """The wire DTO this event serializes to."""
        ...


@dataclass(frozen=True)
class MagnitudeFrame(OutboundEvent, ABC):
    """One spectrum column; subclasses differ only by their wire DTO."""

    spectrum: ToneSpectrum

    def _data(self) -> list[float]:
        return [tone.magnitude for tone in self.spectrum.magnitudes]

    def _ts(self) -> float:
        return self.spectrum.ts.timestamp()


class WaterfallFrame(MagnitudeFrame):
    def to_message(self) -> WaterfallMessage:
        return WaterfallMessage(data=self._data(), ts=self._ts())


class FFTFrame(MagnitudeFrame):
    def to_message(self) -> FFTMessage:
        return FFTMessage(data=self._data(), ts=self._ts())


@dataclass(frozen=True)
class ScopeTrace(OutboundEvent):
    """A run of keying readings, appended to the time-domain trace as one step."""

    samples: tuple[ToneSample, ...]

    def to_message(self) -> OscilloscopeMessage:
        return OscilloscopeMessage(
            data=[float(sample.on) for sample in self.samples],
            mode="append",
            ts=self.samples[-1].ts.timestamp(),
        )


@dataclass(frozen=True)
class DecodedMorse(OutboundEvent):
    element: MorseElement

    def to_message(self) -> MorseMessage:
        return MorseMessage(data=self.element.notation)


@dataclass(frozen=True)
class DecodedText(OutboundEvent):
    text: str

    def to_message(self) -> TextMessage:
        return TextMessage(data=self.text)
