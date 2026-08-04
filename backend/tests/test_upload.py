import json
from collections.abc import AsyncIterator

from morse_decoder.api.file_session import FileSession
from morse_decoder.api.messages import OutboundMessage, TranscriptionMessage
from morse_decoder.pipeline.pipeline import Pipeline


class _StubPipeline(Pipeline):
    def __init__(self, messages: list[OutboundMessage]) -> None:
        self._messages = messages

    async def run(self) -> AsyncIterator[OutboundMessage]:
        for message in self._messages:
            yield message


async def _lines(messages: list[OutboundMessage]) -> list[str]:
    session = FileSession(_StubPipeline(messages))
    return [line async for line in session.run()]


async def test_stream_emits_one_ndjson_line_per_message() -> None:
    lines = await _lines(
        [TranscriptionMessage(data="SOS"), TranscriptionMessage(data="OK")]
    )

    assert all(line.endswith("\n") for line in lines)
    assert [json.loads(line) for line in lines] == [
        {"type": "transcription", "data": "SOS"},
        {"type": "transcription", "data": "OK"},
    ]


async def test_stream_is_empty_when_no_messages() -> None:
    assert await _lines([]) == []
