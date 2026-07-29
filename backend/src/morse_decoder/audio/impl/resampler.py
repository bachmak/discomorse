from collections.abc import Iterator

import numpy as np
import soxr


class Resampler:
    def __init__(self, source_rate: int, target_rate: int) -> None:
        self._stream = soxr.ResampleStream(
            source_rate, target_rate, num_channels=1, dtype="int16"
        )

    def push(self, chunk: bytes) -> bytes:
        return self._resample(np.frombuffer(chunk, dtype=np.int16), last=False)

    def flush(self) -> bytes:
        return self._resample(np.empty(0, dtype=np.int16), last=True)

    def _resample(self, samples: np.ndarray, last: bool) -> bytes:
        return self._stream.resample_chunk(samples, last=last).tobytes()
