from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _EventModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_serialization_defaults_required=True
    )


class MicHandshakeEvent(_EventModel):
    sample_rate: int = Field(gt=0)


class ToneSpectrumEvent(_EventModel):
    type: Literal["tone_spectrum"] = "tone_spectrum"
    data: list[float]
    ts: float


class ToneEvent(_EventModel):
    type: Literal["tone"] = "tone"
    frequency: float
    magnitude: float
    ts: float


class CarrierSampleEvent(_EventModel):
    type: Literal["carrier_sample"] = "carrier_sample"
    frequency: float
    magnitude: float
    is_locked: bool
    ts: float


class NoiseSampleEvent(_EventModel):
    type: Literal["noise_sample"] = "noise_sample"
    magnitude: float
    ts: float


class DigitalToneEvent(_EventModel):
    type: Literal["digital_tone"] = "digital_tone"
    on: bool
    ts: float


class MorseElementEvent(_EventModel):
    type: Literal["morse_element"] = "morse_element"
    data: str


class TranscriptionEvent(_EventModel):
    type: Literal["transcription"] = "transcription"
    data: str


type OutboundEvent = Annotated[
    ToneSpectrumEvent
    | ToneEvent
    | CarrierSampleEvent
    | NoiseSampleEvent
    | DigitalToneEvent
    | MorseElementEvent
    | TranscriptionEvent,
    Field(discriminator="type"),
]

type InboundEvent = MicHandshakeEvent

outbound_event_adapter: TypeAdapter[OutboundEvent] = TypeAdapter(OutboundEvent)
inbound_event_adapter: TypeAdapter[InboundEvent] = TypeAdapter(InboundEvent)


def outbound_event_json_schema() -> dict[str, object]:
    """The JSON schema of every outbound event, for TS codegen."""
    schema = outbound_event_adapter.json_schema(
        mode="serialization", ref_template="#/$defs/{model}"
    )
    schema["title"] = "ServerMessage"
    return schema


def inbound_event_json_schema() -> dict[str, object]:
    """The JSON schema of every inbound event, for TS codegen."""
    schema = inbound_event_adapter.json_schema(ref_template="#/$defs/{model}")
    return schema
