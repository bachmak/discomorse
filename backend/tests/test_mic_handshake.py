import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient
from pydantic import ValidationError

from morse_decoder.api.routes import app
from morse_decoder.api.wire import MicHandshake, client_message_json_schema


@pytest.mark.parametrize(
    "sample_rate",
    [
        pytest.param(48_000, id="chromium-default"),
        pytest.param(44_100, id="cd-rate"),
        pytest.param(8_000, id="already-at-pipeline-rate"),
    ],
)
def test_handshake_accepts_a_positive_sample_rate(sample_rate: int) -> None:
    payload = f'{{"sample_rate": {sample_rate}}}'

    assert MicHandshake.model_validate_json(payload).sample_rate == sample_rate


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param('{"sample_rate": 0}', id="zero"),
        pytest.param('{"sample_rate": -48000}', id="negative"),
        pytest.param('{"sample_rate": 48000.5}', id="fractional"),
        pytest.param('{"sample_rate": "fast"}', id="not-a-number"),
        pytest.param("{}", id="missing-field"),
        pytest.param('{"sample_rate": 48000, "channels": 1}', id="unknown-field"),
        pytest.param("48000", id="bare-value"),
        pytest.param("not json", id="malformed-json"),
    ],
)
def test_handshake_rejects_invalid_payload(payload: str) -> None:
    with pytest.raises(ValidationError):
        MicHandshake.model_validate_json(payload)


def test_client_schema_describes_the_handshake() -> None:
    schema = client_message_json_schema()
    properties = schema["properties"]

    assert schema["title"] == "MicHandshake"
    assert schema["required"] == ["sample_rate"]
    assert schema["additionalProperties"] is False
    assert isinstance(properties, dict)
    assert set(properties) == {"sample_rate"}


def test_mic_socket_closes_when_the_handshake_is_invalid() -> None:
    with TestClient(app).websocket_connect("/ws/mic") as ws:
        ws.send_text('{"sample_rate": 0}')

        with pytest.raises(WebSocketDisconnect):
            ws.receive_text()
