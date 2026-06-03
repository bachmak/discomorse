from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from morse_decoder.pipeline.dto import ToneMagnitudes


class OutboundEvent(ABC):
    """Base for everything the pipeline emits toward the client.

    `to_payload` is the template: every event is wrapped in a `{"type": ...}`
    envelope. Subclasses supply only the tag and their own body.
    """

    wire_type: ClassVar[str]

    def to_payload(self) -> dict[str, object]:
        return {"type": self.wire_type, **self._body()}

    @abstractmethod
    def _body(self) -> dict[str, object]:
        """Event-specific fields, excluding the wire tag."""
        ...


@dataclass(frozen=True)
class MagnitudeFrame(OutboundEvent):
    """A spectrum frame; subclasses differ only by their wire tag."""

    magnitudes: tuple[ToneMagnitudes, ...]

    def _body(self) -> dict[str, object]:
        return {"data": self.magnitudes}


@dataclass(frozen=True)
class WaterfallFrame(MagnitudeFrame):
    wire_type: ClassVar[str] = "waterfall"


@dataclass(frozen=True)
class FFTFrame(MagnitudeFrame):
    wire_type: ClassVar[str] = "fft"


@dataclass(frozen=True)
class DecodedText(OutboundEvent):
    wire_type: ClassVar[str] = "text"
    text: str

    def _body(self) -> dict[str, object]:
        return {"data": self.text}
