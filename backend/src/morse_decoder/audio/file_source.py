import io
from collections.abc import AsyncIterator

import numpy as np
from pydub import AudioSegment

from morse_decoder.audio.base import AudioSource
from morse_decoder.config import settings


class FileSource(AudioSource):
    """Decodes an uploaded audio file and streams Int16 PCM chunks."""

    def __init__(self, data: bytes, fmt: str = "mp3") -> None:
        seg = AudioSegment.from_file(io.BytesIO(data), format=fmt)
        seg = seg.set_frame_rate(settings.audio.sample_rate).set_channels(1).set_sample_width(2)
        self._raw = seg.raw_data

    async def stream(self) -> AsyncIterator[bytes]:  # type: ignore[override]
        chunk = settings.audio.chunk_size * 2  # 2 bytes per Int16 sample
        for i in range(0, len(self._raw), chunk):
            yield self._raw[i : i + chunk]
