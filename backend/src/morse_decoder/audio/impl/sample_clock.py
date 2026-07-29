import datetime

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import PcmChunk


class SampleClock:
    """Maps a running sample count onto wall-clock time."""

    def __init__(self, sample_rate: int, started_at: datetime.datetime) -> None:
        self._sample_rate = sample_rate
        self._started_at = started_at
        self._samples = 0

    def stamp(self, data: bytes) -> PcmChunk:
        chunk = PcmChunk(ts=self._ts(), data=data)
        self._samples += len(data) // PCM16.BYTES_PER_SAMPLE
        return chunk

    def _ts(self) -> datetime.datetime:
        return self._started_at + datetime.timedelta(
            seconds=self._samples / self._sample_rate
        )
