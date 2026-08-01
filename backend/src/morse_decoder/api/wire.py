from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _WireModel(BaseModel):
    """Shared config: reject unknown keys, and treat defaulted fields as always
    present on the wire so the generated TS discriminant is never optional."""

    model_config = ConfigDict(
        extra="forbid", json_schema_serialization_defaults_required=True
    )


class MicHandshake(_WireModel):
    sample_rate: int = Field(gt=0)


class WaterfallMessage(_WireModel):
    type: Literal["waterfall"] = "waterfall"
    data: list[float]
    ts: float


class FFTMessage(_WireModel):
    type: Literal["fft"] = "fft"
    data: list[float]
    ts: float


class OscilloscopeMessage(_WireModel):
    type: Literal["oscilloscope"] = "oscilloscope"
    data: list[float]
    mode: Literal["append", "replace"] | None = None
    ts: float


class MorseMessage(_WireModel):
    """One decoded morse element, written the way it reads in a line of morse."""

    type: Literal["morse"] = "morse"
    data: str


class TextMessage(_WireModel):
    type: Literal["text"] = "text"
    data: str


type ServerMessage = Annotated[
    WaterfallMessage | FFTMessage | OscilloscopeMessage | MorseMessage | TextMessage,
    Field(discriminator="type"),
]

type ClientMessage = MicHandshake

server_message_adapter: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)
client_message_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


def server_message_json_schema() -> dict[str, object]:
    """The JSON schema of every message the server can send, for TS codegen."""
    schema = server_message_adapter.json_schema(
        mode="serialization", ref_template="#/$defs/{model}"
    )
    schema["title"] = "ServerMessage"
    return schema


def client_message_json_schema() -> dict[str, object]:
    """The JSON schema of every message the client can send, for TS codegen."""
    schema = client_message_adapter.json_schema(ref_template="#/$defs/{model}")
    return schema
