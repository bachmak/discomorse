import json
from collections.abc import AsyncIterator

from morse_decoder.api.upload import FileUploadSession
from morse_decoder.pipeline.events import DecodedText, OutboundEvent
from morse_decoder.pipeline.runner import PipelineRunner


class _StubRunner(PipelineRunner):
    def __init__(self, events: list[OutboundEvent]) -> None:
        self._events = events

    async def run(self) -> AsyncIterator[OutboundEvent]:
        for event in self._events:
            yield event


async def _lines(events: list[OutboundEvent]) -> list[str]:
    session = FileUploadSession(_StubRunner(events))
    return [line async for line in session.stream()]


async def test_stream_emits_one_ndjson_line_per_event() -> None:
    lines = await _lines([DecodedText("SOS"), DecodedText("OK")])

    assert all(line.endswith("\n") for line in lines)
    assert [json.loads(line) for line in lines] == [
        {"type": "text", "data": "SOS"},
        {"type": "text", "data": "OK"},
    ]


async def test_stream_is_empty_when_no_events() -> None:
    assert await _lines([]) == []
