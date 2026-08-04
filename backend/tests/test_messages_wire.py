import datetime

import pytest

from morse_decoder.api.messages import outbound_message_json_schema
from morse_decoder.pipeline.dto import (
    CarrierSample,
    Dah,
    DigitalTone,
    Dit,
    InterCharGap,
    IntraCharGap,
    NoiseSample,
    Serializable,
    Tone,
    ToneMagnitude,
    ToneSpectrum,
    Transcription,
    WordGap,
)

_TS = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
_SPECTRUM = ToneSpectrum(
    ts=_TS,
    magnitudes=(
        ToneMagnitude(frequency=10.0, magnitude=0.5),
        ToneMagnitude(frequency=20.0, magnitude=0.25),
    ),
)
_TONE = Tone(frequency=600.0, magnitude=0.75, ts=_TS)


@pytest.mark.parametrize(
    "dto, want",
    [
        pytest.param(
            _SPECTRUM,
            {"type": "tone_spectrum", "data": [0.5, 0.25], "ts": _TS.timestamp()},
            id="tone-spectrum",
        ),
        pytest.param(
            _TONE,
            {
                "type": "tone",
                "frequency": 600.0,
                "magnitude": 0.75,
                "ts": _TS.timestamp(),
            },
            id="tone",
        ),
        pytest.param(
            CarrierSample(tone=_TONE, is_locked=True),
            {
                "type": "carrier_sample",
                "frequency": 600.0,
                "magnitude": 0.75,
                "is_locked": True,
                "ts": _TS.timestamp(),
            },
            id="carrier-sample",
        ),
        pytest.param(
            NoiseSample(noise=0.125, ts=_TS),
            {"type": "noise_sample", "magnitude": 0.125, "ts": _TS.timestamp()},
            id="noise-sample",
        ),
        pytest.param(
            DigitalTone(ts=_TS, on=True),
            {"type": "digital_tone", "on": True, "ts": _TS.timestamp()},
            id="digital-tone",
        ),
        pytest.param(
            Transcription("SOS"),
            {"type": "transcription", "data": "SOS"},
            id="transcription",
        ),
        pytest.param(Dit(), {"type": "morse_element", "data": "."}, id="dit"),
        pytest.param(Dah(), {"type": "morse_element", "data": "-"}, id="dah"),
        pytest.param(
            IntraCharGap(), {"type": "morse_element", "data": ""}, id="intra-char-gap"
        ),
        pytest.param(
            InterCharGap(), {"type": "morse_element", "data": " "}, id="inter-char-gap"
        ),
        pytest.param(
            WordGap(), {"type": "morse_element", "data": " / "}, id="word-gap"
        ),
    ],
)
def test_dto_serializes_to_its_wire_message(
    dto: Serializable, want: dict[str, object]
) -> None:
    assert dto.to_message().model_dump() == want


def test_schema_covers_every_message_type() -> None:
    definitions = outbound_message_json_schema()["$defs"]
    mapping = definitions["OutboundMessage"]["discriminator"]["mapping"]  # type: ignore[index]  # schema is dict[str, object]

    assert set(mapping) == {
        "tone_spectrum",
        "tone",
        "carrier_sample",
        "noise_sample",
        "digital_tone",
        "morse_element",
        "transcription",
    }
