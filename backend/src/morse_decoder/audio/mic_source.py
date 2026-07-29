import asyncio
from collections.abc import AsyncIterator

from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.source import AudioSource


class EndOfStream:
    """Marker pushed onto a source to signal that no more audio will follow."""


MicInput = bytes | EndOfStream


class MicSource(AudioSource):
    """Receives Int16 PCM chunks pushed over a WebSocket."""

    def __init__(self, resampler: Resampler) -> None:
        self._queue: asyncio.Queue[MicInput] = asyncio.Queue()
        self._resampler = resampler

    async def push(self, item: MicInput) -> None:
        await self._queue.put(item)

    async def stream(self) -> AsyncIterator[bytes]:
        while not isinstance(item := await self._queue.get(), EndOfStream):
            if resampled := self._resampler.push(item):
                yield resampled
        if tail := self._resampler.flush():
            yield tail
