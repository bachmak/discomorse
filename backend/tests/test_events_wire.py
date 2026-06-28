import datetime

import pytest

from morse_decoder.api.wire import server_message_json_schema
from morse_decoder.pipeline.dto import ToneMagnitude, ToneSpectrum
from morse_decoder.pipeline.events import (
    DecodedText,
    FFTFrame,
    OutboundEvent,
    WaterfallFrame,
)

_TS = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
_SPECTRUM = ToneSpectrum(
    ts=_TS,
    magnitudes=(
        ToneMagnitude(frequency=10.0, magnitude=0.5),
        ToneMagnitude(frequency=20.0, magnitude=0.25),
    ),
)


@pytest.mark.parametrize(
    "event, want",
    [
        pytest.param(
            WaterfallFrame(_SPECTRUM),
            {"type": "waterfall", "data": [0.5, 0.25], "ts": _TS.timestamp()},
            id="waterfall",
        ),
        pytest.param(
            FFTFrame(_SPECTRUM),
            {"type": "fft", "data": [0.5, 0.25], "ts": _TS.timestamp()},
            id="fft",
        ),
        pytest.param(
            DecodedText("SOS"),
            {"type": "text", "data": "SOS"},
            id="text",
        ),
    ],
)
def test_event_serializes_to_wire_message(
    event: OutboundEvent, want: dict[str, object]
) -> None:
    assert event.to_message().model_dump() == want


def test_schema_covers_every_message_type() -> None:
    schema = server_message_json_schema()
    mapping = schema["discriminator"]["mapping"]  # type: ignore[index]  # schema is dict[str, object]

    assert set(mapping) == {"waterfall", "fft", "oscilloscope", "text"}
