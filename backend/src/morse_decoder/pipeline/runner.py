import time
from collections.abc import AsyncIterator

from morse_decoder.audio.base import AudioSource
from morse_decoder.pipeline.events import (
    DecodedText,
    FFTFrame,
    OutboundEvent,
    WaterfallFrame,
)
from morse_decoder.pipeline.types import ToneSample
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector


class PipelineRunner:
    """Streams audio through detector → decoder → interpreter, yielding events."""

    def __init__(
        self,
        source: AudioSource,
        tone_detector: ToneDetector,
        timing_decoder: TimingDecoder,
        interpreter: Interpreter,
    ) -> None:
        self._source = source
        self._tone_detector = tone_detector
        self._timing_decoder = timing_decoder
        self._interpreter = interpreter

    async def run(self) -> AsyncIterator[OutboundEvent]:
        async for chunk in self._source.stream():
            async for event in self._process_chunk(chunk):
                yield event

    async def _process_chunk(self, chunk: bytes) -> AsyncIterator[OutboundEvent]:
        reading = await self._tone_detector.process(chunk)
        ts = time.monotonic()
        yield FFTFrame(magnitudes=reading.magnitudes, timestamp=ts)
        yield WaterfallFrame(magnitudes=reading.magnitudes, timestamp=ts)
        async for event in self._decode(reading.samples):
            yield event

    async def _decode(
        self, samples: tuple[ToneSample, ...]
    ) -> AsyncIterator[OutboundEvent]:
        events = await self._timing_decoder.process(samples)
        if not events:
            return
        text = await self._interpreter.interpret(events)
        if text:
            yield DecodedText(text)
