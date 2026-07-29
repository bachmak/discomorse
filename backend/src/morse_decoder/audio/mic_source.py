import asyncio
from collections.abc import AsyncIterator

from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import PcmChunk


class EndOfStream:
    """Marker pushed onto a source to signal that no more audio will follow."""


MicInput = bytes | EndOfStream


class MicSource(AudioSource):
    """Receives Int16 PCM chunks pushed over a WebSocket."""

    def __init__(self, resampler: Resampler, sample_clock: SampleClock) -> None:
        self._queue: asyncio.Queue[MicInput] = asyncio.Queue()
        self._resampler = resampler
        self._sample_clock = sample_clock

    async def push(self, item: MicInput) -> None:
        await self._queue.put(item)

    async def stream(self) -> AsyncIterator[PcmChunk]:
        while not isinstance(item := await self._queue.get(), EndOfStream):
            if resampled := self._resampler.push(item):
                yield self._sample_clock.stamp(resampled)
        if tail := self._resampler.flush():
            yield self._sample_clock.stamp(tail)
