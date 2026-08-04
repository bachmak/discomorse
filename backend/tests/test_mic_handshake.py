import pytest
from fastapi import WebSocketDisconnect, status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from morse_decoder.api.messages import MicHandshakeMessage, inbound_message_json_schema
from morse_decoder.api.routes import app

_SUBSCRIPTION = '"subscription": {"channels": ["spectrums"]}'


def _handshake(*fields: str) -> str:
    return f"{{{', '.join(fields)}}}"


@pytest.mark.parametrize(
    "sample_rate",
    [
        pytest.param(48_000, id="chromium-default"),
        pytest.param(44_100, id="cd-rate"),
        pytest.param(8_000, id="already-at-pipeline-rate"),
    ],
)
def test_handshake_accepts_a_positive_sample_rate(sample_rate: int) -> None:
    payload = _handshake(f'"sample_rate": {sample_rate}', _SUBSCRIPTION)

    assert MicHandshakeMessage.model_validate_json(payload).sample_rate == sample_rate


@pytest.mark.parametrize(
    "channels",
    [
        pytest.param("[]", id="no-channel"),
        pytest.param('["corrected_text"]', id="one-channel"),
        pytest.param('["spectrums", "spectrums"]', id="channel-named-twice"),
    ],
)
def test_handshake_accepts_the_channels_it_is_given(channels: str) -> None:
    payload = _handshake(
        '"sample_rate": 48000', f'"subscription": {{"channels": {channels}}}'
    )

    assert MicHandshakeMessage.model_validate_json(payload).subscription.channels <= {
        "spectrums",
        "corrected_text",
    }


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(_handshake('"sample_rate": 0', _SUBSCRIPTION), id="zero"),
        pytest.param(_handshake('"sample_rate": -48000', _SUBSCRIPTION), id="negative"),
        pytest.param(
            _handshake('"sample_rate": 48000.5', _SUBSCRIPTION), id="fractional"
        ),
        pytest.param(
            _handshake('"sample_rate": "fast"', _SUBSCRIPTION), id="not-a-number"
        ),
        pytest.param(_handshake(_SUBSCRIPTION), id="missing-sample-rate"),
        pytest.param(_handshake('"sample_rate": 48000'), id="missing-subscription"),
        pytest.param(
            _handshake('"sample_rate": 48000', '"subscription": {}'),
            id="missing-channels",
        ),
        pytest.param(
            _handshake(
                '"sample_rate": 48000', '"subscription": {"channels": ["gossip"]}'
            ),
            id="unknown-channel",
        ),
        pytest.param(
            _handshake('"sample_rate": 48000', _SUBSCRIPTION, '"channels": 1'),
            id="unknown-field",
        ),
        pytest.param("48000", id="bare-value"),
        pytest.param("not json", id="malformed-json"),
    ],
)
def test_handshake_rejects_invalid_payload(payload: str) -> None:
    with pytest.raises(ValidationError):
        MicHandshakeMessage.model_validate_json(payload)


def test_client_schema_describes_the_handshake() -> None:
    schema = inbound_message_json_schema()
    properties = schema["properties"]

    assert schema["title"] == "MicHandshakeMessage"
    assert schema["required"] == ["sample_rate", "subscription"]
    assert schema["additionalProperties"] is False
    assert isinstance(properties, dict)
    assert set(properties) == {"sample_rate", "subscription"}


def test_mic_socket_closes_when_the_handshake_is_invalid() -> None:
    with TestClient(app).websocket_connect("/ws/mic") as ws:
        ws.send_text(_handshake('"sample_rate": 0', _SUBSCRIPTION))

        with pytest.raises(WebSocketDisconnect) as disconnect:
            ws.receive_text()

    assert disconnect.value.code == status.WS_1008_POLICY_VIOLATION


def test_mic_socket_closes_when_the_first_frame_is_not_text() -> None:
    with TestClient(app).websocket_connect("/ws/mic") as ws:
        ws.send_bytes(b"\x00\x01")

        with pytest.raises(WebSocketDisconnect) as disconnect:
            ws.receive_text()

    assert disconnect.value.code == status.WS_1008_POLICY_VIOLATION


def test_mic_socket_tolerates_a_disconnect_before_the_handshake() -> None:
    """TestClient re-raises server-side errors on exit, so a clean exit is the check."""
    with TestClient(app).websocket_connect("/ws/mic") as ws:
        ws.close()
