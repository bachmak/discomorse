import asyncio
from collections.abc import AsyncIterator

from morse_decoder.audio.base import AudioSource


class BrowserMicSource(AudioSource):
    """Receives Int16 PCM chunks pushed over a WebSocket."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def push(self, chunk: bytes) -> None:
        await self._queue.put(chunk)

    async def stream(self) -> AsyncIterator[bytes]:
        while True:
            yield await self._queue.get()
