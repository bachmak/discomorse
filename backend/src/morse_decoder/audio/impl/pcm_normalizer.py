from math import gcd

import numpy as np
import numpy.typing as npt
from scipy.signal import resample_poly  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.impl.decoder import DecodedAudio
from morse_decoder.audio.pcm16 import PCM16


class PcmNormalizer:
    """Coerces decoded audio to one canonical layout: mono, target rate, Int16 PCM.

    "Normalize" here means format normalization, not loudness/volume normalization.
    """

    def __init__(self, target_rate: int) -> None:
        self._target_rate = target_rate

    def normalize(self, audio: DecodedAudio) -> bytes:
        mono = self._to_mono(audio.samples)
        resampled = self._resample(mono, audio.sample_rate)
        return self._to_int16(resampled).tobytes()

    def _to_mono(self, samples: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        mono: npt.NDArray[np.float32] = samples.mean(axis=1)
        return mono

    def _resample(
        self, mono: npt.NDArray[np.float32], source_rate: int
    ) -> npt.NDArray[np.float64]:
        if source_rate == self._target_rate:
            return mono.astype(np.float64)
        divisor = gcd(source_rate, self._target_rate)
        up, down = self._target_rate // divisor, source_rate // divisor
        resampled: npt.NDArray[np.float64] = resample_poly(mono, up, down)
        return resampled

    def _to_int16(self, samples: npt.NDArray[np.float64]) -> npt.NDArray[PCM16.IntType]:
        clipped = np.clip(samples, -1.0, 1.0)
        return (clipped * PCM16.INT_PEAK).astype(PCM16.IntType)
