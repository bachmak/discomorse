from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _MessageModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_serialization_defaults_required=True
    )


type ChannelName = Literal[
    "spectrums",
    "limited_spectrums",
    "carrier_samples",
    "noise_samples",
    "raw_tones",
    "debounced_tones",
    "morse_elements",
    "transcriptions",
]


class SubscriptionMessage(_MessageModel):
    channels: set[ChannelName]


class MicHandshakeMessage(_MessageModel):
    sample_rate: int = Field(gt=0)
    subscription: SubscriptionMessage


class ToneSpectrumMessage(_MessageModel):
    type: Literal["tone_spectrum"] = "tone_spectrum"
    data: list[float]
    ts: float


class ToneMessage(_MessageModel):
    type: Literal["tone"] = "tone"
    frequency: float
    magnitude: float
    ts: float


class CarrierSampleMessage(_MessageModel):
    type: Literal["carrier_sample"] = "carrier_sample"
    frequency: float
    magnitude: float
    is_locked: bool
    ts: float


class NoiseSampleMessage(_MessageModel):
    type: Literal["noise_sample"] = "noise_sample"
    magnitude: float
    ts: float


class DigitalToneMessage(_MessageModel):
    type: Literal["digital_tone"] = "digital_tone"
    on: bool
    ts: float


class MorseElementMessage(_MessageModel):
    type: Literal["morse_element"] = "morse_element"
    data: str


class TranscriptionMessage(_MessageModel):
    type: Literal["transcription"] = "transcription"
    data: str


type OutboundMessage = Annotated[
    ToneSpectrumMessage
    | ToneMessage
    | CarrierSampleMessage
    | NoiseSampleMessage
    | DigitalToneMessage
    | MorseElementMessage
    | TranscriptionMessage,
    Field(discriminator="type"),
]


class StreamMessage(_MessageModel):
    channel: ChannelName
    payload: OutboundMessage


type InboundMessage = MicHandshakeMessage

outbound_message_adapter: TypeAdapter[StreamMessage] = TypeAdapter(StreamMessage)
inbound_message_adapter: TypeAdapter[InboundMessage] = TypeAdapter(InboundMessage)


def outbound_message_json_schema() -> dict[str, object]:
    """The JSON schema of every outbound message, for TS codegen."""
    schema = outbound_message_adapter.json_schema(
        mode="serialization", ref_template="#/$defs/{model}"
    )
    schema["title"] = "ServerMessage"
    return schema


def inbound_message_json_schema() -> dict[str, object]:
    """The JSON schema of every inbound message, for TS codegen."""
    schema = inbound_message_adapter.json_schema(ref_template="#/$defs/{model}")
    return schema
