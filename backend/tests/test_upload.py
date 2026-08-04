import json
from collections.abc import AsyncIterator

from morse_decoder.api.file_session import FileSession
from morse_decoder.api.messages import StreamMessage, TranscriptionMessage
from morse_decoder.pipeline.pipeline import Pipeline


class _StubPipeline(Pipeline):
    def __init__(self, messages: list[StreamMessage]) -> None:
        self._messages = messages

    async def run(self) -> AsyncIterator[StreamMessage]:
        for message in self._messages:
            yield message


def _transcription(text: str) -> StreamMessage:
    return StreamMessage(
        channel="transcriptions", payload=TranscriptionMessage(data=text)
    )


def _wire(text: str) -> dict[str, object]:
    return {
        "channel": "transcriptions",
        "payload": {"type": "transcription", "data": text},
    }


async def _lines(messages: list[StreamMessage]) -> list[str]:
    session = FileSession(_StubPipeline(messages))
    return [line async for line in session.run()]


async def test_stream_emits_one_ndjson_line_per_message() -> None:
    lines = await _lines([_transcription("SOS"), _transcription("OK")])

    assert all(line.endswith("\n") for line in lines)
    assert [json.loads(line) for line in lines] == [
        _wire("SOS"),
        _wire("OK"),
    ]


async def test_stream_is_empty_when_no_messages() -> None:
    assert await _lines([]) == []
