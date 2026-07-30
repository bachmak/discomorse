import datetime
from dataclasses import dataclass

import numpy as np

from morse_decoder.audio.pcm16 import PCM16


@dataclass(frozen=True)
class FrameBatch:
    """Samples that carry whole frames, plus the wall-clock centre of each frame."""

    samples: np.ndarray
    timestamps: tuple[datetime.datetime, ...]


class FrameStream:
    """Reassembles arbitrarily sized chunks into a gapless grid of frames.

    Chunks arrive at sizes nobody controls, so a frame rarely ends where a chunk
    does. Samples that don't complete a frame stay here and lead the next chunk,
    which keeps every emitted frame filled with real audio instead of padding.
    """

    def __init__(self, frame_length: int, hop_length: int, sample_rate: int) -> None:
        self._frame_length = frame_length
        self._hop_length = hop_length
        self._sample_rate = sample_rate
        self._pending = np.zeros(0, dtype=PCM16.FloatType)

    def push(self, samples: np.ndarray, ts: datetime.datetime) -> FrameBatch:
        origin = ts - self._elapsed(self._pending.size)
        buffered = np.concatenate((self._pending, samples))
        count = self._frame_count(buffered.size)
        self._pending = buffered[count * self._hop_length :].copy()
        return FrameBatch(
            samples=buffered,
            timestamps=tuple(
                origin + self._elapsed(self._centre_offset(index))
                for index in range(count)
            ),
        )

    def _frame_count(self, size: int) -> int:
        if size < self._frame_length:
            return 0
        return 1 + (size - self._frame_length) // self._hop_length

    def _centre_offset(self, index: int) -> float:
        return index * self._hop_length + self._frame_length / 2

    def _elapsed(self, samples: float) -> datetime.timedelta:
        return datetime.timedelta(seconds=samples / self._sample_rate)
