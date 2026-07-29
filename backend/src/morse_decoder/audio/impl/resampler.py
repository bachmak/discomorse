import numpy as np
import numpy.typing as npt
import soxr  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.pcm16 import PCM16


class Resampler:
    def __init__(self, source_rate: int, target_rate: int) -> None:
        self._stream = soxr.ResampleStream(
            source_rate, target_rate, num_channels=1, dtype=PCM16.IntTypeStr
        )

    def push(self, chunk: bytes) -> bytes:
        return self._resample(np.frombuffer(chunk, dtype=PCM16.IntType), last=False)

    def flush(self) -> bytes:
        return self._resample(np.empty(0, dtype=PCM16.IntType), last=True)

    def _resample(self, samples: npt.NDArray[PCM16.IntType], last: bool) -> bytes:
        resampled: npt.NDArray[PCM16.IntType] = self._stream.resample_chunk(
            samples, last=last
        )
        return resampled.tobytes()
