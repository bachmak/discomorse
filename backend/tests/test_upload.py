import json
from collections.abc import AsyncIterator

from morse_decoder.api.events import OutboundEvent, TranscriptionEvent
from morse_decoder.api.file_session import FileSession
from morse_decoder.pipeline.pipeline import Pipeline


class _StubPipeline(Pipeline):
    def __init__(self, events: list[OutboundEvent]) -> None:
        self._events = events

    async def run(self) -> AsyncIterator[OutboundEvent]:
        for event in self._events:
            yield event


async def _lines(events: list[OutboundEvent]) -> list[str]:
    session = FileSession(_StubPipeline(events))
    return [line async for line in session.run()]


async def test_stream_emits_one_ndjson_line_per_event() -> None:
    lines = await _lines(
        [TranscriptionEvent(data="SOS"), TranscriptionEvent(data="OK")]
    )

    assert all(line.endswith("\n") for line in lines)
    assert [json.loads(line) for line in lines] == [
        {"type": "transcription", "data": "SOS"},
        {"type": "transcription", "data": "OK"},
    ]


async def test_stream_is_empty_when_no_events() -> None:
    assert await _lines([]) == []
