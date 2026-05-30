import io
from collections.abc import AsyncIterator

from pydub import AudioSegment  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.base import AudioSource
from morse_decoder.config import AudioSettings


class FileSource(AudioSource):
    """Decodes an uploaded audio file and streams Int16 PCM chunks."""

    def __init__(self, data: bytes, audio: AudioSettings, fmt: str = "mp3") -> None:
        seg = AudioSegment.from_file(io.BytesIO(data), format=fmt)
        seg = (
            seg.set_frame_rate(audio.sample_rate)
            .set_channels(1)
            .set_sample_width(2)
        )
        self._raw = seg.raw_data
        self._chunk = audio.chunk_size * 2  # 2 bytes per Int16 sample

    async def stream(self) -> AsyncIterator[bytes]:
        for i in range(0, len(self._raw), self._chunk):
            yield self._raw[i : i + self._chunk]
