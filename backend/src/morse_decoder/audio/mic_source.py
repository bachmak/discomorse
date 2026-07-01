import asyncio
from collections.abc import AsyncIterator

from morse_decoder.audio.source import AudioSource


class EndOfStream:
    """Marker pushed onto a source to signal that no more audio will follow."""


MicInput = bytes | EndOfStream


class MicSource(AudioSource):
    """Receives Int16 PCM chunks pushed over a WebSocket."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[MicInput] = asyncio.Queue()

    async def push(self, item: MicInput) -> None:
        await self._queue.put(item)

    async def stream(self) -> AsyncIterator[bytes]:
        while not isinstance(item := await self._queue.get(), EndOfStream):
            yield item
